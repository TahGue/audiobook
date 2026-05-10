use tauri::api::process::{Command, CommandEvent};
use tauri::{Manager, Runtime};
use std::sync::Mutex;

// Global state to hold the backend process handle
pub struct BackendState {
  process: Mutex<Option<std::process::Child>>,
}

/// Start the Python backend sidecar
fn start_backend_sidecar<R: Runtime>(app: &tauri::AppHandle<R>) -> Result<(), String> {
  // Get the sidecar binary path
  let sidecar_path = app
    .path_resolver()
    .resolve_resource("binaries/audiobook-backend")
    .ok_or("Could not find backend sidecar binary")?;

  // Spawn the backend process
  let (mut rx, child) = Command::new_sidecar("audiobook-backend")
    .map_err(|e| format!("Failed to create sidecar command: {}", e))?
    .args(["--port", "8001"])
    .spawn()
    .map_err(|e| format!("Failed to spawn backend: {}", e))?;

  // Store process handle in state
  app.state::<BackendState>().process.lock().unwrap().replace(child);

  // Listen to backend output
  tauri::async_runtime::spawn(async move {
    while let Some(event) = rx.recv().await {
      match event {
        CommandEvent::Stdout(line) => {
          println!("Backend: {}", line);
        }
        CommandEvent::Stderr(line) => {
          eprintln!("Backend Error: {}", line);
        }
        CommandEvent::Terminated(payload) => {
          println!("Backend terminated: {:?}", payload);
        }
        _ => {}
      }
    }
  });

  // Give the backend a moment to start
  std::thread::sleep(std::time::Duration::from_secs(2));
  
  println!("Python backend started on port 8001");
  Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .manage(BackendState {
      process: Mutex::new(None),
    })
    .setup(|app| {
      // Try to start the backend sidecar (only in production builds)
      if !cfg!(debug_assertions) {
        if let Err(e) = start_backend_sidecar(&app.handle()) {
          eprintln!("Warning: Could not start backend sidecar: {}", e);
          eprintln!("Make sure you're running the backend separately with: uvicorn main:app --port 8001");
        }
      } else {
        println!("Development mode: Backend should be started manually with: uvicorn main:app --port 8001");
      }

      // Add logging plugin in debug mode
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      Ok(())
    })
    .on_window_event(|event| {
      // Clean up backend process when window is closed
      if let tauri::WindowEvent::Destroyed = event.event() {
        if let Some(child) = event.window().state::<BackendState>().process.lock().unwrap().take() {
          let _ = child.kill();
          println!("Backend process terminated");
        }
      }
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
