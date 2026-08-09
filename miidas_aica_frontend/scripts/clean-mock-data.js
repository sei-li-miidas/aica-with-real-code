/**
 * Script to remove mock API responses from the build directory
 */
import { existsSync, rmSync } from "fs";
import { join } from "path";
import { fileURLToPath } from "url";
import { dirname } from "path";

// Get current directory in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Path to the mock API responses in the build directory
const mockDir = join(dirname(__dirname), "build", "mock");

// Check if the directory exists and remove it
if (existsSync(mockDir)) {
  try {
    rmSync(mockDir, { recursive: true, force: true });
    console.debug("✅ Successfully removed mock API responses from build");
  } catch (error) {
    console.error("❌ Error removing mock API responses:", error);
    process.exit(1);
  }
} else {
  console.debug("ℹ️ No mock API responses found in build directory");
}
