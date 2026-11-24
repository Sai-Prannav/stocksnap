# Advanced Image Detection Configuration Guide

This document explains the configuration options available for the enhanced image detection system.

## Environment Variables

### Core AI/ML Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `YOLO_MODEL_NAME` | `yolov8n.pt` | YOLO model filename (yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt) |
| `YOLO_CONFIDENCE_THRESHOLD` | `0.5` | Minimum confidence for YOLO detections (0.0-1.0) |
| `YOLO_IOU_THRESHOLD` | `0.45` | IoU threshold for Non-Maximum Suppression |
| `YOLO_MAX_DETECTIONS` | `100` | Maximum number of detections per image |
| `YOLO_DEVICE` | `cpu` | Device for inference (cpu, cuda, mps) |
| `YOLO_ENSEMBLE_ENABLED` | `false` | Enable ensemble of multiple YOLO models |

### SAM (Segment Anything Model) Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SAM_MODEL_NAME` | `sam_vit_h_4b8939.pth` | SAM model filename |
| `SAM_CONFIDENCE_THRESHOLD` | `0.7` | Confidence threshold for SAM masks |
| `SAM_DEVICE` | `cpu` | Device for SAM inference |
| `SAM_ENABLED` | `false` | Enable SAM segmentation (requires additional setup) |

### General AI Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_IMAGE_SIZE` | `1920` | Maximum image dimension for processing |
| `ENABLE_GPU` | `false` | Enable GPU acceleration when available |
| `BATCH_SIZE` | `1` | Batch size for processing multiple images |

### Advanced Preprocessing Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_ADVANCED_PREPROCESSING` | `true` | Enable advanced preprocessing pipeline |
| `ANGLE_CORRECTION_ENABLED` | `true` | Enable shelf angle correction |
| `LIGHTING_NORMALIZATION_ENABLED` | `true` | Enable lighting normalization |
| `IMAGE_ENHANCEMENT_ENABLED` | `true` | Enable image enhancement |
| `MULTI_SCALE_ENABLED` | `false` | Enable multi-scale processing |

### Quality Assurance Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_CONFIDENCE_THRESHOLD` | `0.3` | Minimum confidence for final detections |
| `MAX_DETECTIONS_LIMIT` | `50` | Maximum number of detections after QA |

### Performance Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_PERFORMANCE_MONITORING` | `true` | Enable detailed performance logging |
| `LOG_DETAILED_METRICS` | `true` | Log detailed processing metrics |

## Configuration Files

### YAML Configuration (Alternative)

You can also create a `config.yaml` file for more complex configurations:

```yaml
# config.yaml
ai_models:
  yolo:
    model_name: "yolov8n.pt"
    confidence_threshold: 0.5
    iou_threshold: 0.45
    max_detections: 100
    device: "cpu"
    ensemble:
      enabled: false
      models: ["yolov8n.pt", "yolov8s.pt"]
      weights: [0.6, 0.4]
  
  sam:
    model_name: "sam_vit_h_4b8939.pth"
    confidence_threshold: 0.7
    device: "cpu"
    enabled: false

preprocessing:
  angle_correction:
    enabled: true
    method: "hough_transform"
    angle_tolerance: 5.0
    min_line_length: 100
    max_line_gap: 10
  
  lighting_normalization:
    enabled: true
    method: "clahe"
    clip_limit: 2.0
    tile_grid_size: [8, 8]
  
  enhancement:
    enabled: true
    sharpening: true
    noise_reduction: true
    contrast_enhancement: true
  
  multi_scale:
    enabled: false
    scales: [0.8, 1.0, 1.2]
    merge_method: "weighted_average"

quality_assurance:
  enabled: true
  min_confidence: 0.3
  max_detections: 50
  validate_results: true

intelligent_counting:
  enabled: true
  shelf_detection: true
  pattern_recognition: true
  size_filtering: true

performance:
  enable_monitoring: true
  log_detailed_metrics: true
  track_processing_time: true
```

## Performance Tuning

### For Better Accuracy
- Increase `YOLO_CONFIDENCE_THRESHOLD` to reduce false positives
- Enable `ANGLE_CORRECTION_ENABLED` for angled shelf photos
- Enable `LIGHTING_NORMALIZATION_ENABLED` for varying lighting conditions
- Set `MULTI_SCALE_ENABLED=true` for items of different sizes

### For Better Speed
- Use smaller YOLO model (`yolov8n.pt`)
- Decrease `MAX_IMAGE_SIZE`
- Disable advanced preprocessing features
- Set `ENABLE_PERFORMANCE_MONITORING=false`

### For GPU Acceleration
- Set `ENABLE_GPU=true`
- Install PyTorch with CUDA support
- Set `YOLO_DEVICE=cuda` and `SAM_DEVICE=cuda`

## Advanced Features

### Custom Model Training
To use custom-trained models:
1. Place your model file in `models/yolo/` directory
2. Update `YOLO_MODEL_NAME` to your model filename
3. Update class mappings in `ModelManager._get_class_label()`

### SAM Integration
To enable SAM segmentation:
1. Install SAM: `pip install segment-anything`
2. Download SAM model to `models/sam/` directory
3. Set `SAM_ENABLED=true`
4. Configure `SAM_MODEL_NAME`

### Ensemble Models
To enable ensemble detection:
1. Set `YOLO_ENSEMBLE_ENABLED=true`
2. Configure multiple models in ensemble section
3. Adjust weights for model combination

## Troubleshooting

### Common Issues

1. **Memory Errors**: Reduce `MAX_IMAGE_SIZE` or disable advanced features
2. **Slow Processing**: Disable `MULTI_SCALE_ENABLED` and use smaller models
3. **Poor Detection**: Lower confidence thresholds or enable angle correction
4. **GPU Not Working**: Verify CUDA installation and set `ENABLE_GPU=true`

### Debug Mode
Enable detailed logging:
```bash
export LOG_DETAILED_METRICS=true
export ENABLE_PERFORMANCE_MONITORING=true
```

### Performance Monitoring
Check system status:
```bash
curl http://localhost:8000/api/scans/ai-status
```

## Deployment Considerations

### Production Settings
```bash
# Optimized for production
ENABLE_GPU=true
YOLO_MODEL_NAME=yolov8s.pt
MAX_IMAGE_SIZE=1280
ENABLE_ADVANCED_PREPROCESSING=true
MULTI_SCALE_ENABLED=false
ENABLE_PERFORMANCE_MONITORING=false
```

### Development Settings
```bash
# Optimized for development
ENABLE_GPU=false
YOLO_MODEL_NAME=yolov8n.pt
MAX_IMAGE_SIZE=1920
ENABLE_ADVANCED_PREPROCESSING=true
MULTI_SCALE_ENABLED=true
ENABLE_PERFORMANCE_MONITORING=true
LOG_DETAILED_METRICS=true
```
