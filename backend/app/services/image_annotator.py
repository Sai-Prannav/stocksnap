import os
from PIL import Image, ImageDraw

class ImageAnnotator:
    def __init__(self):
        # Ensure the directory for annotated images exists
        self.output_dir = os.path.join("uploads", "annotated")
        os.makedirs(self.output_dir, exist_ok=True)

    def annotate_image_with_boxes(self, image_path, detections):
        """
        image_path: Path to the original image
        detections: List of dicts like {'box': [x1, y1, x2, y2], 'label': 'bottle', 'conf': 0.85}
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if it's in another mode (like RGBA)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                draw = ImageDraw.Draw(img)
                width, height = img.size

                for det in detections:
                    # YOLO usually returns normalized coordinates (0 to 1)
                    # We convert them to actual pixel values
                    x1, y1, x2, y2 = det['box']
                    
                    # If coordinates are normalized, scale them
                    if max(x1, y1, x2, y2) <= 1.0:
                        left = x1 * width
                        top = y1 * height
                        right = x2 * width
                        bottom = y2 * height
                    else:
                        left, top, right, bottom = x1, y1, x2, y2

                    # Draw the thick bounding box
                    # We use a bright color (like Neon Green) for the demo
                    draw.rectangle([left, top, right, bottom], outline="#FF0000", width=4)

                # Save the processed image
                filename = os.path.basename(image_path)
                output_path = os.path.join(self.output_dir, f"annotated_{filename}")
                img.save(output_path)
                
                return output_path
        except Exception as e:
            print(f"Error annotating image: {e}")
            return None