import torch
from src.models.model_factory import ModelFactory

factory = ModelFactory()
model = factory.create_model('unet', in_channels=6, num_classes=2)
checkpoint = torch.load('data/weights/change_unet_best.pt', map_location='cpu', weights_only=True)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

with torch.no_grad():
    zeros = torch.zeros((1, 6, 256, 256))
    out = model(zeros)
    pred = torch.argmax(out, dim=1)
    print('Unique classes for Change UNet all zeros:', torch.unique(pred).tolist())
