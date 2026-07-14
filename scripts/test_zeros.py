import torch
from src.models.model_factory import ModelFactory

factory = ModelFactory()
model = factory.create_model('deeplabv3plus', in_channels=12, num_classes=6)
checkpoint = torch.load('data/weights/deeplabv3plus_best.pt', map_location='cpu', weights_only=True)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

with torch.no_grad():
    zeros = torch.zeros((1, 12, 256, 256))
    out = model(zeros)
    pred = torch.argmax(out, dim=1)
    print('Unique classes for all zeros:', torch.unique(pred).tolist())
