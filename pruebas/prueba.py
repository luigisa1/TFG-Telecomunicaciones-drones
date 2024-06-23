import torch

iou_vect = torch.tensor([])

for i in range(5):
    iou=torch.tensor(i)
    iou_vect = torch.cat((iou_vect, iou.unsqueeze(0)))
print(iou_vect)

indices=torch.where(iou_vect>6)
print(indices)