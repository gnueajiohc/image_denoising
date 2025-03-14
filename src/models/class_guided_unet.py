import torch
import torch.nn as nn

FEATURE_CHANNELS = 32

class ClassGuidedUNet(nn.Module):
    """
    Class Guided U-Net Model (default dataset is STL10)
    
    Args:
        classifier (nn.Module): classifier class (ClassifyingCNN or ClassifyingResNet)
        unet (DenoisingUNet): U-Net class
        feature_channels (int): the num of feature channels
    """
    def __init__(self, classifier, unet, feature_channels=FEATURE_CHANNELS):
        
        super(ClassGuidedUNet, self).__init__()
        self.classifier = classifier
        self.unet = unet
        
        # classifier output (10) -> (FEATURE_CHANNELS * 12 * 12)
        # Unfortunately, 12 looks like a magic number here...
        # We have 12 because STL10 has width 96 and we have 4 layers with stride 2 as a default in UNet class
        self.fc = nn.Linear(10, out_features=feature_channels * 12 * 12)
        
        for param in self.classifier.parameters():
            param.requires_grad = False
    
    def forward(self, x):
        """forward propagation function"""
        # classifier parameters are fixed
        with torch.no_grad():
            class_out = self.classifier(x)
        
        class_out = self.fc(class_out)
        class_out = class_out.view(-1, self.fc.out_features // (12 * 12), 12, 12)
        
        x = self.unet(x, class_out)
        return x