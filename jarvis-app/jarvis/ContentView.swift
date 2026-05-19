//
//  ContentView.swift
//  jarvis
//
//  Created by ellkaden on 10/05/26.
//
import SwiftUI
import Combine

struct ContentView: View {
    var body: some View {
        JARVISView()
    }
}

struct JARVISView: View {
    @ObservedObject var viewModel = JARVISViewModel()
    @FocusState private var isInputFocused: Bool
    @State private var showDashboard = false

    var body: some View {
        ZStack {
            // фон
            Color(red: 0.008, green: 0.016, blue: 0.031)
                .ignoresSafeArea()

            // сетка как у Iron Man
            GridBackground()
                .ignoresSafeArea()

            VStack(spacing: 0) {
                headerView
                messagesView
                inputView
            }
        }
        .preferredColorScheme(.dark)
    }

    // MARK: - Header
    var headerView: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("JARVIS")
                    .font(.system(size: 20, weight: .bold, design: .monospaced))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.white, Color(red: 0.29, green: 0.62, blue: 0.88)],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                Text("JUST A RATHER VERY INTELLIGENT SYSTEM")
                    .font(.system(size: 7, design: .monospaced))
                    .foregroundColor(Color(red: 0.1, green: 0.23, blue: 0.35))
                    .kerning(1.5)
            }
            Spacer()
            HStack(spacing: 8) {
                // Demo/Live button
                Button(action: { viewModel.toggleMode() }) {
                    HStack(spacing: 4) {
                        Circle()
                            .fill(viewModel.isDemoMode ? Color.green : Color.red)
                            .frame(width: 6, height: 6)
                        Text(viewModel.isDemoMode ? "DEMO" : "LIVE")
                            .font(.system(size: 9, weight: .medium, design: .monospaced))
                            .kerning(0.8)
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(
                        RoundedRectangle(cornerRadius: 3)
                            .stroke(viewModel.isDemoMode ? Color.green.opacity(0.3) : Color.red.opacity(0.3), lineWidth: 1)
                            .background(
                                RoundedRectangle(cornerRadius: 3)
                                    .fill(viewModel.isDemoMode ? Color.green.opacity(0.08) : Color.red.opacity(0.08))
                            )
                    )
                }
                .foregroundColor(viewModel.isDemoMode ? .green : .red)
                // Arc Reactor
                ArcReactorView(
                    isListening: viewModel.isRecording,
                    isProcessing: viewModel.isProcessing,
                    isConnected: viewModel.isConnected
                )
                .frame(width: 36, height: 36)
            }
        }
        .padding(.horizontal, 20)
        .padding(.top, 16)
        .padding(.bottom, 12)
        .overlay(
            Rectangle()
                .fill(
                    LinearGradient(
                        colors: [.clear, Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.3), .clear],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .frame(height: 1),
            alignment: .bottom
        )
    }

    // MARK: - Messages
    var messagesView: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 14) {
                    ForEach(viewModel.messages) { message in
                        MessageBubbleView(message: message)
                            .id(message.id)
                    }
                    if viewModel.isProcessing {
                        ProcessingView()
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 16)
            }
            .onChange(of: viewModel.messages.count) { _ in
                if let last = viewModel.messages.last {
                    withAnimation(.easeOut(duration: 0.3)) {
                        proxy.scrollTo(last.id, anchor: .bottom)
                    }
                }
            }
        }
    }

    // MARK: - Input
    var inputView: some View {
        VStack(spacing: 12) {
            Text(viewModel.isRecording ? "● RECORDING" : viewModel.isProcessing ? "⚡ PROCESSING" : "HOLD TO SPEAK")
                .font(.system(size: 9, design: .monospaced))
                .foregroundColor(
                    viewModel.isRecording ? .green :
                    viewModel.isProcessing ? Color(red: 0.96, green: 0.62, blue: 0.04) :
                    Color(red: 0.1, green: 0.23, blue: 0.35)
                )
                .kerning(1.5)

            // кнопка микрофона
            ZStack {
                // внешнее кольцо
                Circle()
                    .stroke(
                        viewModel.isRecording ?
                        Color.green.opacity(0.2) :
                        Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.08),
                        lineWidth: 1
                    )
                    .frame(width: 76, height: 76)

                // основная кнопка
                Circle()
                    .fill(
                        viewModel.isRecording ?
                        Color.green.opacity(0.08) :
                        Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.04)
                    )
                    .frame(width: 64, height: 64)
                    .overlay(
                        Circle()
                            .stroke(
                                viewModel.isRecording ?
                                Color.green.opacity(0.5) :
                                Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.2),
                                lineWidth: 1
                            )
                    )

                Image(systemName: viewModel.isRecording ? "waveform" : "mic")
                    .font(.system(size: 22, weight: .light))
                    .foregroundColor(
                        viewModel.isRecording ? .green :
                        Color(red: 0.29, green: 0.62, blue: 0.88)
                    )
            }
            .scaleEffect(viewModel.isRecording ? 1.08 : 1.0)
            .animation(.easeInOut(duration: 0.2), value: viewModel.isRecording)
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { _ in if !viewModel.isRecording { viewModel.startRecording() } }
                    .onEnded { _ in viewModel.stopRecording() }
            )

            // текстовый ввод
            HStack(spacing: 8) {
                TextField("", text: $viewModel.inputText)
                    .placeholder(when: viewModel.inputText.isEmpty) {
                        Text("type a command...")
                            .font(.system(size: 13, design: .monospaced))
                            .foregroundColor(Color(red: 0.1, green: 0.23, blue: 0.35))
                    }
                    .font(.system(size: 13, design: .monospaced))
                    .foregroundColor(.white)
                    .focused($isInputFocused)
                    .onSubmit { viewModel.sendText() }
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(
                        RoundedRectangle(cornerRadius: 3)
                            .fill(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.04))
                            .overlay(
                                RoundedRectangle(cornerRadius: 3)
                                    .stroke(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.1), lineWidth: 1)
                            )
                    )

                Button(action: {
                    viewModel.sendText()
                    isInputFocused = false
                }) {
                    Image(systemName: "arrow.up")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(Color(red: 0.29, green: 0.62, blue: 0.88))
                        .frame(width: 40, height: 40)
                        .background(
                            RoundedRectangle(cornerRadius: 3)
                                .fill(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.08))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 3)
                                        .stroke(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.25), lineWidth: 1)
                                )
                        )
                }
                .disabled(viewModel.inputText.isEmpty)
                .opacity(viewModel.inputText.isEmpty ? 0.3 : 1.0)
            }
            .padding(.horizontal, 16)
        }
        .padding(.vertical, 14)
        .overlay(
            Rectangle()
                .fill(
                    LinearGradient(
                        colors: [.clear, Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.2), .clear],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .frame(height: 1),
            alignment: .top
        )
        .onTapGesture { isInputFocused = false }
    }
}

// MARK: - Grid Background
struct GridBackground: View {
    var body: some View {
        Canvas { context, size in
            let gridSize: CGFloat = 40
            let color = Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.03)

            var x: CGFloat = 0
            while x <= size.width {
                context.stroke(Path { p in p.move(to: CGPoint(x: x, y: 0)); p.addLine(to: CGPoint(x: x, y: size.height)) }, with: .color(color), lineWidth: 0.5)
                x += gridSize
            }
            var y: CGFloat = 0
            while y <= size.height {
                context.stroke(Path { p in p.move(to: CGPoint(x: 0, y: y)); p.addLine(to: CGPoint(x: size.width, y: y)) }, with: .color(color), lineWidth: 0.5)
                y += gridSize
            }
        }
    }
}

// MARK: - Arc Reactor
struct ArcReactorView: View {
    let isListening: Bool
    let isProcessing: Bool
    let isConnected: Bool

    @State private var rotation1: Double = 0
    @State private var rotation2: Double = 0

    var body: some View {
        ZStack {
            Circle()
                .stroke(coreColor.opacity(0.15), lineWidth: 1)
                .frame(width: 36, height: 36)
                .rotationEffect(.degrees(rotation1))

            Circle()
                .stroke(coreColor.opacity(0.25), lineWidth: 1)
                .frame(width: 26, height: 26)
                .rotationEffect(.degrees(rotation2))

            Circle()
                .stroke(coreColor.opacity(0.4), lineWidth: 1)
                .frame(width: 18, height: 18)

            Circle()
                .fill(RadialGradient(
                    colors: [coreColor, coreColor.opacity(0.6)],
                    center: .center,
                    startRadius: 0,
                    endRadius: 5
                ))
                .frame(width: 8, height: 8)
                .shadow(color: coreColor.opacity(0.8), radius: 4)
        }
        .onAppear {
            withAnimation(.linear(duration: 10).repeatForever(autoreverses: false)) { rotation1 = 360 }
            withAnimation(.linear(duration: 5).repeatForever(autoreverses: false)) { rotation2 = -360 }
        }
    }

    var coreColor: Color {
        if isListening { return .green }
        if isProcessing { return Color(red: 0.96, green: 0.62, blue: 0.04) }
        if isConnected { return Color(red: 0.29, green: 0.62, blue: 0.88) }
        return Color(white: 0.2)
    }
}

// MARK: - Message Bubble
struct MessageBubbleView: View {
    let message: JARVISMessage

    var body: some View {
        HStack(alignment: .top, spacing: 0) {
            if message.isUser {
                Spacer(minLength: 60)
                Text(message.text)
                    .font(.system(size: 13))
                    .foregroundColor(.black)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(Color.white.opacity(0.9))
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
//                    .background(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.05))
//                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
//                    .overlay(
//                        RoundedRectangle(cornerRadius: 18, style: .continuous)
//                    .stroke(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.15), lineWidth: 1)
//                    .background(Color.white.opacity(0.9))
//                    
//                    )
                
            } else {
                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 6) {
                        Text("JARVIS")
                            .font(.system(size: 9, weight: .semibold, design: .monospaced))
                            .foregroundColor(Color(red: 0.29, green: 0.62, blue: 0.88))
                            .kerning(1.5)
                        if message.isProactive {
                            Text("ALERT")
                                .font(.system(size: 8, design: .monospaced))
                                .foregroundColor(Color(red: 0.96, green: 0.62, blue: 0.04))
                                .padding(.horizontal, 5)
                                .padding(.vertical, 1)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 2)
                                        .stroke(Color(red: 0.96, green: 0.62, blue: 0.04).opacity(0.4), lineWidth: 1)
                                )
                        }
                    }
                    Text(message.text)
                        .font(.system(size: 13))
                        .foregroundColor(Color(white: 0.85))
                        .padding(.horizontal, 14)
                        .padding(.vertical, 10)
                        .background(
                            message.isProactive ?
                            Color(red: 0.96, green: 0.62, blue: 0.04).opacity(0.05) :
                            Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.05)
                        )
                        .background(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.05))
                        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 18, style: .continuous)
                                .stroke(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.15), lineWidth: 1)
                        )
                }
                Spacer(minLength: 40)
            }
        }
    }
}

// MARK: - Processing View
struct ProcessingView: View {
    @State private var animate = false

    var body: some View {
        HStack(alignment: .top, spacing: 0) {
            VStack(alignment: .leading, spacing: 4) {
                Text("JARVIS")
                    .font(.system(size: 9, weight: .semibold, design: .monospaced))
                    .foregroundColor(Color(red: 0.29, green: 0.62, blue: 0.88))
                    .kerning(1.5)
                HStack(spacing: 5) {
                    ForEach(0..<3) { i in
                        Circle()
                            .fill(Color(red: 0.29, green: 0.62, blue: 0.88))
                            .frame(width: 5, height: 5)
                            .opacity(animate ? 1.0 : 0.2)
                            .animation(.easeInOut(duration: 0.6).repeatForever().delay(Double(i) * 0.2), value: animate)
                    }
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 12)
                .background(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.05))
                .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.15), lineWidth: 1)
                )
            }
            Spacer()
        }
        .onAppear { animate = true }
    }
}

// MARK: - Placeholder extension
extension View {
    func placeholder<Content: View>(when shouldShow: Bool, @ViewBuilder placeholder: () -> Content) -> some View {
        ZStack(alignment: .leading) {
            placeholder().opacity(shouldShow ? 1 : 0)
            self
        }
    }
}
