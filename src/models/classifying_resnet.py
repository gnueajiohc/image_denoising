import torch
import torch.nn as nn
import torch.nn.functional as F

# -----------------------------------
# ResNet Basic Block class
# -----------------------------------
class BasicBlock(nn.Module):
    """
    Basic residual block for ResNet
    
    This block performs 2 consecutive 3x3 convoultional with ReLU activation, plus a skip connection
    
    Args:
        in_channels (int):
        out_channels (int):
        use_batchnorm (bool):
    """
    def __init__(
        self,
        in_channels,
        out_channels,
        kernel_size=3,
        stride=1,
        use_batchnorm=False
    ):
        super(BasicBlock, self).__init__()
        
        # list for 1st convolution block layers
        conv_block1 = []
        conv_block1.append(nn.Conv2d(in_channels,
                                     out_channels,
                                     kernel_size=kernel_size,
                                     stride=stride,
                                     padding=kernel_size // 2,
                                     bias=not use_batchnorm))
        if use_batchnorm:
            conv_block1.append(nn.BatchNorm2d(out_channels))
        self.conv1 = nn.Sequential(*conv_block1)
        
        # list for 2nd convolution block layers
        conv_block2 = []
        conv_block2.append(nn.Conv2d(out_channels,
                                     out_channels,
                                     kernel_size=kernel_size,
                                     stride=1,
                                     padding=kernel_size // 2,
                                     bias=not use_batchnorm))
        self.conv2 = nn.Sequential(*conv_block2)
        
        if use_batchnorm:
            conv_block2.append(nn.BatchNorm2d(out_channels))
        
        # skip connection: if channel sizes differ, we need a 1x1 conv
        self.shortcut = nn.Sequential()
        if (stride != 1) or (in_channels != out_channels):
            shortcut_layers = [
                nn.Conv2d(in_channels, out_channels,
                          kernel_size=1, stride=stride, bias=False)
            ]
            if use_batchnorm:
                shortcut_layers.append(nn.BatchNorm2d(out_channels))
            self.shortcut = nn.Sequential(*shortcut_layers)
    
    def forward(self, x):
        """forward propagation function"""
        identity = self.shortcut(x)
        
        out = self.conv1(x)
        out = F.relu(out, inplace=True)
        
        out = self.conv2(out)
        
        out += identity
        out = F.relu(out, inplace=True)
        
        return out

# -----------------------------------
# Classifying ResNet Model class
# -----------------------------------
class ClassifyingResNet(nn.Module):
    """
    Classifying ResNet Model (default dataset is STL10)
    
    Args:
        in_channels (int): the num of input image channels
        num_classes (int): the num of label classes
        block_channels (list[int]): the num of hidden layers' channels
        num_blocks (list[int]): the num of basic blocks
        strides (list[int]): stride value of each block
        use_batchnorm (bool): whether to use batch normalization
    """
    def __init__(
        self,
        in_channels=3,
        num_classes=10,
        block_channels=[16,32,64,128],
        num_blocks=[2, 2, 2, 2],
        strides=[2, 1, 1, 1],
        use_batchnorm=True
    ):
        super(ClassifyingResNet, self).__init__()
        
        self.use_batchnorm=use_batchnorm
        
        # list for conv block layers
        conv_block = []
        conv_block.append(nn.Conv2d(in_channels=in_channels,
                                    out_channels=in_channels,
                                    kernel_size=7,
                                    stride=2,
                                    padding=3,
                                    bias=not use_batchnorm))
        if use_batchnorm:
            conv_block.append(nn.BatchNorm2d(in_channels))
        self.conv_block = nn.Sequential(*conv_block)
        
        self.max_pool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        
        # ResNet layers (layer1 ~ layer4)
        self.layer1 = self._make_layer(in_channels,       block_channels[0], num_blocks[0], strides[0])
        self.layer2 = self._make_layer(block_channels[0], block_channels[1], num_blocks[1], strides[1])
        self.layer3 = self._make_layer(block_channels[1], block_channels[2], num_blocks[2], strides[2])
        self.layer4 = self._make_layer(block_channels[2], block_channels[3], num_blocks[3], strides[3])
        
        # Global average pooling
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Final fully connected layer
        self.fc = nn.Linear(block_channels[-1], num_classes)
    
    def _make_layer(self, in_channels, out_channels, block_count, stride):
        """make ResNet layer from 'in_channels' to 'out_channels'"""
        layers = []
        # at least one block
        layers.append(
            BasicBlock(
                in_channels=in_channels,
                out_channels=out_channels,
                stride=stride,
                use_batchnorm=self.use_batchnorm
            )
        )
        
        for _ in range(1, block_count):
            layers.append(
                BasicBlock(
                    in_channels=out_channels,
                    out_channels=out_channels,
                    stride=stride,
                    use_batchnorm=self.use_batchnorm
                )
            )
        return nn.Sequential(*layers)

    def forward(self, x):
        """forward propagation function"""
        # stem
        x = self.conv_block(x)
        x = self.max_pool(x)
        x = F.relu(x, inplace=True)
        
        # res layers
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        
        # last part
        x = self.global_pool(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)
        
        return x
        