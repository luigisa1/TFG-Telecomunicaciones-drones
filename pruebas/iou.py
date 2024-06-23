import torch

def calcular_iou_tensor(caja1, caja2):
    # Suponiendo que caja1 y caja2 son tensores de la forma [x1, y1, x2, y2]

    # Calcula las coordenadas de la intersección de las dos cajas
    x1_inter = torch.max(caja1[0], caja2[0])
    y1_inter = torch.max(caja1[1], caja2[1])
    x2_inter = torch.min(caja1[2], caja2[2])
    y2_inter = torch.min(caja1[3], caja2[3])

    # Calcula el área de la intersección
    ancho_inter = torch.clamp(x2_inter - x1_inter, min=0)
    alto_inter = torch.clamp(y2_inter - y1_inter, min=0)
    area_interseccion = ancho_inter * alto_inter

    # Calcula el área de la primera caja
    ancho_caja1 = caja1[2] - caja1[0]
    alto_caja1 = caja1[3] - caja1[1]
    area_caja1 = ancho_caja1 * alto_caja1

    # Calcula el área de la segunda caja
    ancho_caja2 = caja2[2] - caja2[0]
    alto_caja2 = caja2[3] - caja2[1]
    area_caja2 = ancho_caja2 * alto_caja2

    # Calcula el área de la unión
    area_union = area_caja1 + area_caja2 - area_interseccion

    # Calcula la IoU
    iou = area_interseccion / area_union if area_union > 0 else 0

    return iou

caja1 = torch.tensor([100, 100, 300, 300])
caja2 = torch.tensor([200, 200, 400, 400])

iou = calcular_iou_tensor(caja1, caja2)
print(f"La IoU entre las dos cajas es: {iou}")
