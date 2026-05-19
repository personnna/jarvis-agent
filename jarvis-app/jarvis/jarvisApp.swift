//
//  jarvisApp.swift
//  jarvis
//
//  Created by ellkaden on 10/05/26.
//

import SwiftUI
import SwiftData
import UniformTypeIdentifiers

@main
struct jarvisApp: App {
    var body: some Scene {
        WindowGroup {
            MainTabView()
        }
    }
}

struct MainTabView: View {
    
    @ObservedObject private var viewModel = JARVISViewModel()

    var body: some View {
        TabView {
            JARVISView(viewModel: viewModel)
                .tabItem {
                    Image(systemName: "waveform")
                    Text("JARVIS")
                }

            DashboardView(serverURL: "\(viewModel.serverURL):\(viewModel.port)")
                .tabItem {
                    Image(systemName: "square.grid.2x2")
                    Text("Dashboard")
                }
        }
        .tint(Color(red: 0.29, green: 0.62, blue: 0.88))
        .preferredColorScheme(.dark)
        .onAppear {
            let appearance = UITabBarAppearance()
            appearance.configureWithOpaqueBackground()
            appearance.backgroundColor = UIColor(red: 0.008, green: 0.016, blue: 0.031, alpha: 1)
            appearance.stackedLayoutAppearance.normal.iconColor = UIColor(white: 0.3, alpha: 1)
            appearance.stackedLayoutAppearance.normal.titleTextAttributes = [.foregroundColor: UIColor(white: 0.3, alpha: 1)]
            appearance.stackedLayoutAppearance.selected.iconColor = UIColor(red: 0.29, green: 0.62, blue: 0.88, alpha: 1)
            appearance.stackedLayoutAppearance.selected.titleTextAttributes = [.foregroundColor: UIColor(red: 0.29, green: 0.62, blue: 0.88, alpha: 1)]
            UITabBar.appearance().standardAppearance = appearance
            UITabBar.appearance().scrollEdgeAppearance = appearance
        }
    }
}

extension UTType {
    static var itemDocument: UTType {
        UTType(importedAs: "com.example.item-document")
    }
}

struct jarvisMigrationPlan: SchemaMigrationPlan {
    static var schemas: [VersionedSchema.Type] = [
        jarvisVersionedSchema.self,
    ]

    static var stages: [MigrationStage] = [
        // Stages of migration between VersionedSchema, if required.
    ]
}

struct jarvisVersionedSchema: VersionedSchema {
    static var versionIdentifier = Schema.Version(1, 0, 0)

    static var models: [any PersistentModel.Type] = [
        Item.self,
    ]
}
