import os
import sys
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent.parent))


def convert_voc_to_yolo(xml_path: str, img_width: int, img_height: int) -> str:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    lines = []
    for obj in root.iter("object"):
        name = obj.find("name").text
        if name != "number_plate":
            continue
        bndbox = obj.find("bndbox")
        xmin = float(bndbox.find("xmin").text)
        ymin = float(bndbox.find("ymin").text)
        xmax = float(bndbox.find("xmax").text)
        ymax = float(bndbox.find("ymax").text)

        cx = ((xmin + xmax) / 2) / img_width
        cy = ((ymin + ymax) / 2) / img_height
        w = (xmax - xmin) / img_width
        h = (ymax - ymin) / img_height

        cx = max(0.0, min(1.0, cx))
        cy = max(0.0, min(1.0, cy))
        w = max(0.001, min(1.0, w))
        h = max(0.001, min(1.0, h))

        lines.append(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    return "\n".join(lines)


def convert_numberplate_dataset():
    print("=== Converting Number Plate Dataset to YOLO Format ===")

    base = Path("datasets/numberplate")
    xml_dir = base / "Annotations" / "Annotations"
    img_dir = base / "Indian_Number_Plates" / "Sample_Images"

    yolo_base = base / "yolo_format"
    train_img = yolo_base / "images" / "train"
    train_lbl = yolo_base / "labels" / "train"
    val_img = yolo_base / "images" / "val"
    val_lbl = yolo_base / "labels" / "val"

    for d in [train_img, train_lbl, val_img, val_lbl]:
        d.mkdir(parents=True, exist_ok=True)

    xml_files = list(xml_dir.glob("*.xml"))
    print(f"Found {len(xml_files)} XML annotations")

    xml_files_sorted = sorted(xml_files, key=lambda x: x.stem)
    split_idx = int(len(xml_files_sorted) * 0.8)

    converted = 0
    for i, xml_path in enumerate(xml_files_sorted):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            size = root.find("size")
            img_w = int(float(size.find("width").text))
            img_h = int(float(size.find("height").text))

            filename = root.find("filename").text
            img_path = img_dir / filename

            if not img_path.exists():
                for ext in [".jpg", ".jpeg", ".png"]:
                    candidate = img_dir / (xml_path.stem + ext)
                    if candidate.exists():
                        img_path = candidate
                        break
                else:
                    continue

            yolo_label = convert_voc_to_yolo(str(xml_path), img_w, img_h)
            if not yolo_label:
                continue

            if i < split_idx:
                dst_img = train_img / img_path.name
                dst_lbl = train_lbl / (xml_path.stem + ".txt")
            else:
                dst_img = val_img / img_path.name
                dst_lbl = val_lbl / (xml_path.stem + ".txt")

            shutil.copy2(str(img_path), str(dst_img))
            with open(dst_lbl, "w") as f:
                f.write(yolo_label)
            converted += 1
        except Exception as e:
            print(f"Error converting {xml_path.name}: {e}")

    print(f"Converted {converted} images")

    data_yaml = yolo_base / "data.yaml"
    with open(data_yaml, "w") as f:
        f.write(f"""train: {train_img}
val: {val_img}
nc: 1
names: ['number_plate']
""")
    print(f"Created data.yaml: {data_yaml}")

    return str(data_yaml)


def convert_traffic_light_dataset():
    print("\n=== Converting Traffic Light Dataset ===")

    base = Path("datasets/traffic_light/carla_traffic_light_dataset")
    img_dir = base / "img"
    csv_path = base / "label.csv"

    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        return None

    import csv
    labels = {}
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            img_name = row.get("filename") or row.get("image") or row.get("img")
            label_id = row.get("label_id") or row.get("label") or row.get("class") or row.get("category")
            if img_name and label_id is not None:
                labels[img_name] = int(label_id)

    if not labels:
        print("Could not parse CSV labels")
        return None

    print(f"  Label distribution: { {k: v for k, v in sorted(set(labels.values()), key=lambda x: labels.values().count(x))} if len(labels) < 100 else 'too many to show'} ")

    yolo_base = base / "yolo_format"
    train_img = yolo_base / "images" / "train"
    train_lbl = yolo_base / "labels" / "train"
    val_img = yolo_base / "images" / "val"
    val_lbl = yolo_base / "labels" / "val"

    for d in [train_img, train_lbl, val_img, val_lbl]:
        d.mkdir(parents=True, exist_ok=True)

    all_images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))
    print(f"Found {len(all_images)} images, {len(labels)} labels")

    split_idx = int(len(all_images) * 0.8)
    converted = 0

    for i, img_path in enumerate(sorted(all_images)):
        class_id = labels.get(img_path.name)
        if class_id is None:
            continue

        if i < split_idx:
            dst_img = train_img / img_path.name
            dst_lbl = train_lbl / (img_path.stem + ".txt")
        else:
            dst_img = val_img / img_path.name
            dst_lbl = val_lbl / (img_path.stem + ".txt")

        shutil.copy2(str(img_path), str(dst_img))
        with open(dst_lbl, "w") as f:
            f.write(str(class_id))
        converted += 1

    print(f"Converted {converted} images")

    data_yaml = yolo_base / "data.yaml"
    with open(data_yaml, "w") as f:
        f.write(f"""train: {train_img}
val: {val_img}
nc: 5
names: ['red', 'yellow', 'green', 'unknown', 'not_traffic_light']
""")
    print(f"Created data.yaml: {data_yaml}")
    return str(data_yaml)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "numberplate":
            convert_numberplate_dataset()
        elif sys.argv[1] == "traffic_light":
            convert_traffic_light_dataset()
    else:
        convert_numberplate_dataset()
        convert_traffic_light_dataset()
