"""3-QADAM: modelning aniqligini o'lchash (portfolio uchun eng muhim raqam).

Har bir odam rasmlarining 80% i o'qitishga, 20% i testga ajratiladi.
Model test rasmlarini hech qachon ko'rmagan bo'ladi.

Ishga tushirish:  python evaluate.py
"""
import random

from config import THRESHOLD
from train import load_dataset, train_model

TEST_RATIO = 0.2
SEED = 42  # har safar bir xil bo'linish uchun


def split(data):
    rng = random.Random(SEED)
    train, test = {}, []
    for name, images in data.items():
        images = images[:]
        rng.shuffle(images)
        n_test = max(1, int(len(images) * TEST_RATIO))
        train[name] = images[n_test:]
        test.extend((name, img) for img in images[:n_test])
    return train, test


def main():
    data = load_dataset()
    if len(data) < 2:
        print("Kamida 2 kishi kerak.")
        return

    train, test = split(data)
    recognizer, names = train_model(train)

    results = []  # (haqiqiy ism, taxmin qilingan ism, distance)
    for true_name, img in test:
        label, distance = recognizer.predict(img)
        results.append((true_name, names[label], distance))

    correct = sum(t == p for t, p, _ in results)
    print(f"Odamlar: {len(names)}   Test rasmlari: {len(results)}")
    print(f"Aniqlik (chegarasiz): {correct / len(results):.1%}\n")

    # Chegara (threshold) ta'siri: past chegara = kam xato, lekin ko'proq "Unknown"
    print(f"{'Chegara':>8} | {'Qabul qilindi':>13} | {'Qabul qilinganlarda aniqlik':>27}")
    print("-" * 56)
    for th in (40, 50, 60, 70, 80, 90, 100):
        accepted = [(t, p) for t, p, d in results if d < th]
        acc = sum(t == p for t, p in accepted) / len(accepted) if accepted else 0
        mark = "  <- hozirgi" if th == THRESHOLD else ""
        print(f"{th:>8} | {len(accepted) / len(results):>13.1%} | {acc:>27.1%}{mark}")

    print("\nOdam bo'yicha:")
    for name in names.values():
        mine = [(t, p) for t, p, _ in results if t == name]
        ok = sum(t == p for t, p in mine)
        print(f"  {name:<25} {ok}/{len(mine)}")


if __name__ == "__main__":
    main()
