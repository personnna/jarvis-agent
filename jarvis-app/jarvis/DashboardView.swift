//
//  DashboardView.swift
//  jarvis
//
//  Created by ellkaden on 16/05/26.
//


import SwiftUI

struct DashboardView: View {
    @State private var dashData: DashboardData?
    @State private var loading = true
    @State private var refreshing = false
    @Environment(\.dismiss) private var dismiss

    let serverURL: String

    var body: some View {
        ZStack {
            Color(red: 0.008, green: 0.016, blue: 0.031).ignoresSafeArea()
            GridBackground().ignoresSafeArea()

            if loading {
                loadingView
            } else {
                ScrollView {
                    VStack(spacing: 0) {
                        headerView
                        timeView
                        if let data = dashData {
                            LazyVStack(spacing: 12) {
                                weatherCard(data.weather)
                                scheduleCard(data.calendar)
                                tasksCard(data.jira)
                            }
                            .padding(16)
                        }
                    }
                }
            }
        }
        .onAppear { fetchData() }
    }

    var loadingView: some View {
        VStack(spacing: 12) {
            ProgressView()
                .tint(Color(red: 0.29, green: 0.62, blue: 0.88))
            Text("INITIALIZING")
                .font(.system(size: 10, design: .monospaced))
                .foregroundColor(Color(red: 0.29, green: 0.62, blue: 0.88))
                .kerning(2)
        }
    }

    var headerView: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("JARVIS")
                    .font(.system(size: 16, weight: .bold, design: .monospaced))
                    .foregroundColor(Color(red: 0.29, green: 0.62, blue: 0.88))
                    .kerning(2)
                Text("LIFE DASHBOARD")
                    .font(.system(size: 8, design: .monospaced))
                    .foregroundColor(Color(red: 0.1, green: 0.23, blue: 0.35))
                    .kerning(1.5)
            }
            Spacer()
            HStack(spacing: 10) {
                Button(action: { fetchData() }) {
                    Image(systemName: refreshing ? "arrow.clockwise" : "arrow.clockwise")
                        .font(.system(size: 14))
                        .foregroundColor(Color(red: 0.29, green: 0.62, blue: 0.88))
                        .rotationEffect(.degrees(refreshing ? 360 : 0))
                        .animation(refreshing ? .linear(duration: 1).repeatForever(autoreverses: false) : .default, value: refreshing)
                }
                Button(action: { dismiss() }) {
                    Text("← CHAT")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(Color(red: 0.29, green: 0.62, blue: 0.88))
                        .kerning(0.8)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .overlay(
                            RoundedRectangle(cornerRadius: 3)
                                .stroke(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.3), lineWidth: 1)
                        )
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .overlay(
            Rectangle()
                .fill(LinearGradient(
                    colors: [.clear, Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.25), .clear],
                    startPoint: .leading, endPoint: .trailing
                ))
                .frame(height: 1),
            alignment: .bottom
        )
    }

    var timeView: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(dashData?.time ?? "--:--")
                    .font(.system(size: 52, weight: .ultraLight))
                    .foregroundColor(.white)
                    .monospacedDigit()
                Text(dashData?.date ?? "")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundColor(Color(red: 0.29, green: 0.62, blue: 0.88))
                    .kerning(1)
            }
            Spacer()
            ZStack {
                Circle()
                    .stroke(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.2), lineWidth: 1)
                    .frame(width: 48, height: 48)
                VStack(spacing: 3) {
                    Circle()
                        .fill(Color.green)
                        .frame(width: 7, height: 7)
                        .shadow(color: .green, radius: 3)
                    Text("ONLINE")
                        .font(.system(size: 7, design: .monospaced))
                        .foregroundColor(.green)
                        .kerning(0.5)
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 16)
        .overlay(
            Rectangle()
                .fill(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.06))
                .frame(height: 1),
            alignment: .bottom
        )
    }

    func weatherCard(_ text: String) -> some View {
        let tempMatch = text.range(of: #"\d+°C"#, options: .regularExpression)
        let temp = tempMatch.map { String(text[$0]).replacingOccurrences(of: "°C", with: "") } ?? "--"
        let isRain = text.lowercased().contains("rain")
        let isSun = text.lowercased().contains("sun") || text.lowercased().contains("clear")
        let icon = isRain ? "cloud.rain" : isSun ? "sun.max" : "cloud"
        let shortDesc = text.components(separatedBy: ".").first ?? ""

        return DashCard(label: "⚡ ENVIRONMENT") {
            HStack(alignment: .top, spacing: 12) {
                VStack(alignment: .leading, spacing: 4) {
                    HStack(alignment: .firstTextBaseline, spacing: 4) {
                        Image(systemName: icon)
                            .font(.system(size: 24))
                            .foregroundColor(Color(red: 0.29, green: 0.62, blue: 0.88))
                        Text("\(temp)°")
                            .font(.system(size: 42, weight: .ultraLight))
                            .foregroundColor(.white)
                            .monospacedDigit()
                    }
                    Text("📍 Mestre, Italy")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(Color(red: 0.29, green: 0.62, blue: 0.88))
                    Text(shortDesc)
                        .font(.system(size: 11))
                        .foregroundColor(Color(white: 0.5))
                        .lineLimit(2)
                }
                Spacer()
            }
        }
    }

    func scheduleCard(_ text: String) -> some View {
        let lines = text.split(separator: "\n")
            .map(String.init)
            .filter { $0.hasPrefix("•") }

        return DashCard(label: "📡 SCHEDULE", count: "\(lines.count) EVENTS") {
            VStack(spacing: 6) {
                ForEach(Array(lines.prefix(6).enumerated()), id: \.offset) { _, line in
                    let parts = line.replacingOccurrences(of: "• ", with: "").components(separatedBy: " — ")
                    HStack(spacing: 10) {
                        Text(parts.first ?? "")
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundColor(Color(red: 0.29, green: 0.62, blue: 0.88))
                            .frame(width: 130, alignment: .leading)
                        Text(parts.last ?? "")
                            .font(.system(size: 11))
                            .foregroundColor(Color(white: 0.75))
                            .lineLimit(1)
                        Spacer()
                    }
                    .padding(.vertical, 5)
                    .padding(.horizontal, 10)
                    .background(Color(white: 0.05))
                    .cornerRadius(4)
                }
            }
        }
    }

    func tasksCard(_ text: String) -> some View {
        let lines = text.split(separator: "\n")
            .map(String.init)
            .filter { $0.hasPrefix("•") }

        return DashCard(label: "🎯 ACTIVE TASKS", count: "\(lines.count) OPEN") {
            VStack(spacing: 6) {
                ForEach(Array(lines.prefix(5).enumerated()), id: \.offset) { _, line in
                    let clean = line.replacingOccurrences(of: "• ", with: "")
                    let parts = clean.components(separatedBy: ":")
                    let id = parts.first?.trimmingCharacters(in: .whitespaces) ?? ""
                    let rest = parts.dropFirst().joined(separator: ":").components(separatedBy: "[").first?.trimmingCharacters(in: .whitespaces) ?? ""

                    HStack(spacing: 8) {
                        Rectangle()
                            .fill(Color(red: 0, green: 0.32, blue: 0.8))
                            .frame(width: 2)
                        Text(id)
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundColor(Color(red: 0.2, green: 0.5, blue: 1.0))
                            .frame(width: 52, alignment: .leading)
                        Text(rest)
                            .font(.system(size: 11))
                            .foregroundColor(Color(white: 0.75))
                            .lineLimit(1)
                        Spacer()
                        Text("TO DO")
                            .font(.system(size: 8, design: .monospaced))
                            .foregroundColor(Color(white: 0.3))
                            .padding(.horizontal, 5)
                            .padding(.vertical, 2)
                            .overlay(
                                RoundedRectangle(cornerRadius: 2)
                                    .stroke(Color(white: 0.15), lineWidth: 1)
                            )
                    }
                    .padding(.vertical, 5)
                    .padding(.horizontal, 8)
                    .background(Color(red: 0, green: 0.32, blue: 0.8).opacity(0.05))
                    .cornerRadius(4)
                }
            }
        }
    }

    func fetchData() {
        refreshing = true
        guard let url = URL(string: "http://\(serverURL)/dashboard") else { return }
        URLSession.shared.dataTask(with: url) { data, _, _ in
            DispatchQueue.main.async {
                self.refreshing = false
                self.loading = false
                guard let data = data,
                      let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return }
                self.dashData = DashboardData(
                    time: json["time"] as? String ?? "",
                    date: json["date"] as? String ?? "",
                    weather: json["weather"] as? String ?? "",
                    calendar: json["calendar"] as? String ?? "",
                    jira: json["jira"] as? String ?? ""
                )
            }
        }.resume()
    }
}

struct DashboardData {
    let time: String
    let date: String
    let weather: String
    let calendar: String
    let jira: String
}

struct DashCard<Content: View>: View {
    let label: String
    var count: String? = nil
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(label)
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundColor(Color(red: 0.29, green: 0.62, blue: 0.88))
                    .kerning(1.5)
                Spacer()
                if let count = count {
                    Text(count)
                        .font(.system(size: 9, design: .monospaced))
                        .foregroundColor(Color(red: 0.1, green: 0.23, blue: 0.35))
                        .kerning(0.8)
                }
            }
            content
        }
        .padding(14)
        .background(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.02))
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.1), lineWidth: 1)
        )
        .cornerRadius(6)
        .overlay(
            Rectangle()
                .fill(LinearGradient(
                    colors: [.clear, Color(red: 0.29, green: 0.62, blue: 0.88).opacity(0.25), .clear],
                    startPoint: .leading, endPoint: .trailing
                ))
                .frame(height: 1),
            alignment: .top
        )
    }
}
