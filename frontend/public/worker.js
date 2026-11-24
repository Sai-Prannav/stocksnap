// frontend/public/worker.js
import { pipeline, env } from "https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2";

// This tells the library NOT to look for local files and use the Web instead
env.allowLocalModels = false;
env.useBrowserCache = true;

let detector;

// Initialize the model
const init = async () =>
     {
    if (!detector) {
        // We use a small, fast model for hackathons (detr-resnet-50)
        detector = await pipeline('object-detection', 'Xenova/detr-resnet-50');
        console.log("✅ AI Model Loaded & Ready");
    }
};

self.onmessage = async (event) => {
    await init();
    const { image } = event.data;
    
    // Run detection
    const output = await detector(image, {
        threshold: 0.5,
        percentage: true,
    });

    // Send results back to the UI
    self.postMessage({
        status: 'complete',
        output: output
    });
};