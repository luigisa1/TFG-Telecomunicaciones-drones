# ------------------------- CÓDIGO PROVISIONAL PARA PASAR A MODELO INT8 -----------------

from ultralytics import YOLO

model=YOLO("train6.pt")

model.export(format='engine',device=0,int8=True)