//
//  JARVISViewModel.swift
//  jarvis
//
//  Created by ellkaden on 10/05/26.
//

import SwiftUI
import Combine
import AVFoundation


struct JARVISMessage: Identifiable {
    let id = UUID()
    let text: String
    let isUser: Bool
    let isProactive: Bool = false
}

class JARVISViewModel: NSObject, ObservableObject {
    @Published var messages: [JARVISMessage] = []
    @Published var inputText: String = ""
    @Published var isConnected: Bool = false
    @Published var isRecording: Bool = false
    @Published var isProcessing: Bool = false
    @Published var isDemoMode: Bool = false
    
    // замени на свой IP из ipconfig getifaddr en0
    let serverURL = "140.82.58.192"
    let port = "8000"
    private let synthesizer = AVSpeechSynthesizer()
    
    private var webSocket: URLSessionWebSocketTask?
    private var audioRecorder: AVAudioRecorder?
    private var recordingURL: URL?
    
    override init() {
        super.init()
        connectWebSocket()
    }
    
    // MARK: - WebSocket
    func connectWebSocket() {
        guard let url = URL(string: "ws://\(serverURL):\(port)/ws") else { return }
        print("[JARVIS] Connecting to \(url)")
        let session = URLSession(configuration: .default)
        webSocket = session.webSocketTask(with: url)
        webSocket?.resume()
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.isConnected = true
            self.receiveMessage()
            self.startPing()
        }
    }
    
    func receiveMessage() {
        webSocket?.receive { [weak self] result in
            switch result {
            case .success(let message):
                if case .string(let text) = message,
                   let data = text.data(using: .utf8),
                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let msg = json["message"] as? String {
                    DispatchQueue.main.async {
                        self?.addMessage(msg, isUser: false)
                        self?.isProcessing = false
                    }
                }
                self?.receiveMessage()
            case .failure:
                DispatchQueue.main.async { self?.isConnected = false }
                DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                    self?.connectWebSocket()
                }
            }
        }
    }
    
    func sendText() {
        guard !inputText.isEmpty else { return }
        let text = inputText
        print("[JARVIS] Sending: \(text)")
        addMessage(text, isUser: true)
        inputText = ""
        isProcessing = true

        let payload = ["text": text]
        guard let data = try? JSONSerialization.data(withJSONObject: payload),
              let string = String(data: data, encoding: .utf8) else { return }

        if webSocket?.state != .running {
            print("[JARVIS] Not connected, reconnecting...")
            connectWebSocket()
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                self.webSocket?.send(.string(string)) { error in
                    if let error = error {
                        print("[JARVIS] Send error after reconnect: \(error.localizedDescription)")
                    } else {
                        print("[JARVIS] Sent successfully after reconnect")
                    }
                }
            }
            return
        }

        webSocket?.send(.string(string)) { error in
            if let error = error {
                print("[JARVIS] Send error: \(error.localizedDescription)")
            } else {
                print("[JARVIS] Sent successfully")
            }
        }
    }
    
    // MARK: - Voice
    func startRecording() {
        
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("jarvis_audio.m4a")
        recordingURL = url
        
        #if os(iOS)
        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.record, mode: .default)
        try? session.setActive(true)
        #endif

        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 16000.0,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]
        audioRecorder = try? AVAudioRecorder(url: url, settings: settings)
        audioRecorder?.record()
        DispatchQueue.main.async { self.isRecording = true }
    }
    
    func startPing() {
        DispatchQueue.global().asyncAfter(deadline: .now() + 20) { [weak self] in
            self?.webSocket?.sendPing { error in
                if error == nil {
                    self?.startPing()
                }
            }
        }
    }
    
    func toggleMode() {
        let newMode = isDemoMode ? "live" : "demo"
        guard let url = URL(string: "http://\(serverURL):\(port)/mode/\(newMode)") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        URLSession.shared.dataTask(with: request) { [weak self] _, _, _ in
            DispatchQueue.main.async {
                self?.isDemoMode = !self!.isDemoMode
                
            }
        }.resume()
    }
    
    func stopRecording() {
        audioRecorder?.stop()
        DispatchQueue.main.async {
            self.isRecording = false
            self.isProcessing = true
        }
        guard let url = recordingURL else { return }
        DispatchQueue.global().asyncAfter(deadline: .now() + 0.3) {
            self.sendVoice(url: url)
        }
    }
    
    func sendVoice(url: URL) {
        guard let audioData = try? Data(contentsOf: url) else { return }
        
        var request = URLRequest(url: URL(string: "http://\(serverURL):\(port)/voice")!)
        request.httpMethod = "POST"
        request.timeoutInterval = 120
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"audio.wav\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/m4a\r\n\r\n".data(using: .utf8)!)
        body.append(audioData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 120
        config.timeoutIntervalForResource = 180
        let session = URLSession(configuration: config)
        
        session.dataTask(with: request) { [weak self] data, _, _ in
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                DispatchQueue.main.async { self?.isProcessing = false }
                return
            }
            if let transcript = json["transcript"] as? String,
               !transcript.isEmpty,
               !transcript.lowercased().contains("error") {
                DispatchQueue.main.async { self?.addMessage(transcript, isUser: true) }
            }
            if let response = json["response"] as? String,
               !response.lowercased().contains("error submitting") {
                DispatchQueue.main.async {
                    self?.addMessage(response, isUser: false)
                    self?.isProcessing = false
                }
            } else {
                DispatchQueue.main.async { self?.isProcessing = false }
            }
        }.resume()
    }
    
    func speak(_ text: String) {
        DispatchQueue.global(qos: .userInitiated).async {
            let shortText = String(text.prefix(300))
            let utterance = AVSpeechUtterance(string: shortText)
            utterance.voice = AVSpeechSynthesisVoice(language: "en-GB")
            utterance.rate = 0.52
            utterance.pitchMultiplier = 0.85
            utterance.volume = 1.0
            DispatchQueue.main.async {
                self.synthesizer.speak(utterance)
            }
        }
    }
    
    func addMessage(_ text: String, isUser: Bool) {
        messages.append(JARVISMessage(text: text, isUser: isUser))
        if !isUser {
            speak(text)
        }
    }
}
