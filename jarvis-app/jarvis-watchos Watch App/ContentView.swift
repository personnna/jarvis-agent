//
//  ContentView.swift
//  jarvis-watchos Watch App
//
//  Created by ellkaden on 16/05/26.
//

import SwiftUI
import WatchKit
import AVFoundation
import Combine

struct ContentView: View {
    @StateObject private var vm = WatchViewModel()
    
    var body: some View {
        ZStack {
            Color(red: 0.008, green: 0.016, blue: 0.031)
                .ignoresSafeArea()

            VStack(spacing: 12) {
                Spacer()

                Button(action: { vm.handleTap() }) {
                    ZStack {
                        Circle()
                            .stroke(vm.ringColor.opacity(0.15), lineWidth: 1)
                            .frame(width: 100, height: 100)

                        Circle()
                            .stroke(vm.ringColor.opacity(0.3), lineWidth: 1)
                            .frame(width: 76, height: 76)
                            .rotationEffect(.degrees(vm.rotation1))

                        Circle()
                            .stroke(vm.ringColor.opacity(0.5), lineWidth: 1)
                            .frame(width: 54, height: 54)
                            .rotationEffect(.degrees(vm.rotation2))

                        Circle()
                            .fill(RadialGradient(
                                colors: [vm.ringColor, vm.ringColor.opacity(0.4)],
                                center: .center,
                                startRadius: 0,
                                endRadius: 16
                            ))
                            .frame(width: 28, height: 28)
                            .shadow(color: vm.ringColor.opacity(0.8), radius: 8)
                    }
                }
                .buttonStyle(.plain)
                .simultaneousGesture(
                    DragGesture(minimumDistance: 0)
                        .onChanged { _ in
                            if !vm.isListening && !vm.isProcessing {
                                vm.startRecording()
                            }
                        }
                        .onEnded { _ in
                            vm.stopRecording()
                        }
                )
                .animation(.easeInOut(duration: 0.3), value: vm.isListening)

                // Статус
                Text(vm.statusText)
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundColor(vm.ringColor.opacity(0.8))
                    .kerning(1)
                    .multilineTextAlignment(.center)
                    .frame(maxWidth: .infinity)

                Spacer()
            }
            .padding()
        }
        .onAppear { vm.startRotation() }
    }
}

class WatchViewModel: NSObject, ObservableObject {    
    @Published var isListening = false
    @Published var isProcessing = false
    @Published var isSpeaking = false
    @Published var rotation1: Double = 0
    @Published var rotation2: Double = 0
    private var isSending = false
    
    override init() {
        super.init()
    }

    private let serverURL = "140.82.58.192"
    private let port = "8000"
    private var audioRecorder: AVAudioRecorder?
    private var recordingURL: URL?
    private let synthesizer = AVSpeechSynthesizer()

    var ringColor: Color {
        if isListening { return .green }
        if isProcessing { return Color(red: 0.96, green: 0.62, blue: 0.04) }
        if isSpeaking { return Color(red: 0.29, green: 0.62, blue: 0.88) }
        return Color(red: 0.29, green: 0.62, blue: 0.88)
    }

    var statusText: String {
        if isListening { return "LISTENING" }
        if isProcessing { return "THINKING" }
        if isSpeaking { return "SPEAKING" }
        return "TAP TO SPEAK"
    }

    func startRotation() {
        withAnimation(.linear(duration: 8).repeatForever(autoreverses: false)) {
            rotation1 = 360
        }
        withAnimation(.linear(duration: 4).repeatForever(autoreverses: false)) {
            rotation2 = -360
        }
    }

    func handleTap() {
        if isListening {
            stopRecording()
        } else if !isProcessing {
            startRecording()
        }
        WKInterfaceDevice.current().play(.click)
    }

    func startRecording() {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("jarvis_watch.m4a")
        recordingURL = url

        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 16000.0,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]

        audioRecorder = try? AVAudioRecorder(url: url, settings: settings)
        audioRecorder?.record()

        DispatchQueue.main.async { self.isListening = true }

        // авто-стоп через 8 секунд
        DispatchQueue.main.asyncAfter(deadline: .now() + 8) {
            if self.isListening { self.stopRecording() }
        }
    }

    func stopRecording() {
        guard !isSending else { return }
        isSending = true
        audioRecorder?.stop()
        DispatchQueue.main.async {
            self.isListening = false
            self.isProcessing = true
        }
        guard let url = recordingURL else { return }
        DispatchQueue.global().asyncAfter(deadline: .now() + 0.3) {
            self.sendVoice(url: url)
        }
    }

    func sendVoice(url: URL) {
        print("[WATCH] Starting sendVoice")
        guard let audioData = try? Data(contentsOf: url) else {
            print("[WATCH] Failed to read audio data")
            DispatchQueue.main.async { self.isProcessing = false }
            return
        }
        print("[WATCH] Audio size: \(audioData.count) bytes")

        var request = URLRequest(url: URL(string: "http://\(serverURL):\(port)/voice")!)
        request.httpMethod = "POST"
        request.timeoutInterval = 60

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"audio.m4a\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/m4a\r\n\r\n".data(using: .utf8)!)
        body.append(audioData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            if let error = error {
                print("[WATCH] Network error: \(error.localizedDescription)")
                DispatchQueue.main.async { self?.isProcessing = false }
                return
            }
            if let httpResponse = response as? HTTPURLResponse {
                print("[WATCH] HTTP status: \(httpResponse.statusCode)")
            }
            guard let data = data else {
                print("[WATCH] No data received")
                DispatchQueue.main.async { self?.isProcessing = false }
                return
            }
            print("[WATCH] Response: \(String(data: data, encoding: .utf8) ?? "unreadable")")

            guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                print("[WATCH] JSON parse failed")
                DispatchQueue.main.async { self?.isProcessing = false }
                return
            }

            let response = json["response"] as? String ?? ""
            let transcript = json["transcript"] as? String ?? ""
            print("[WATCH] Transcript: \(transcript)")
            print("[WATCH] Response: \(response)")

            DispatchQueue.main.async {
                self?.isProcessing = false
                self?.isSending = false
                if !response.isEmpty && !response.contains("error") {
                    self?.speak(response)
                }
            }
        }.resume()
    }

    func speak(_ text: String) {
        DispatchQueue.main.async { self.isSpeaking = true }
        WKInterfaceDevice.current().play(.success)
        
        let clean = String(text.prefix(150))
        let utterance = AVSpeechUtterance(string: clean)
        utterance.voice = AVSpeechSynthesisVoice(language: "en-GB")
        utterance.rate = 0.5
        utterance.volume = 1.0
        
        DispatchQueue.main.async {
            self.synthesizer.speak(utterance)
        }
        
        DispatchQueue.main.asyncAfter(deadline: .now() + Double(clean.count) / 12) {
            self.isSpeaking = false
            self.isSending = false
        }
    }
}
