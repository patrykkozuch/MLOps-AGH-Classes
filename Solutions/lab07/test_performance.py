import requests
import time
text = "The elderly, distinguished professor, Dr. Alistair Finch, known internationally for his groundbreaking research into late-nineteenth-century Neo-Gothic architectural revival movements, and moreover, his surprising, perhaps even eccentric, habit of wearing a vividly colored, hand-knitted scarf, even during the oppressive heat of midsummer academic conferences, a truly peculiar choice that often drew whispered comments and speculative glances from his more conservatively dressed, tweed-jacket-wearing colleagues, including the notoriously critical Dr. Evelyn Reed, who specialized in early Byzantine mosaics and considered Finch’s fashion sense a regrettable distraction from serious intellectual pursuits, slowly, deliberately, and with an air of profound, almost religious contemplation—which suggested the immense weight of the information he was about to deliver to the assembled student body and faculty members, a group encompassing nervous undergraduates, jaded graduate researchers working tirelessly on their dissertations, and skeptical tenured department heads—stepped up to the podium, adjusted the microphone, cleared his throat with a resonant, theatrical sound that echoed momentarily throughout the vast, high-ceilinged lecture hall, and finally, after what felt like an eternity to the impatient audience gathered there, began to speak about the recently discovered, remarkably preserved, and potentially world-altering archives pertaining to the elusive master builder, Elias Thorne."
def test_service(url, name):
    times = []
    for i in range(100):
        start = time.time()
        response = requests.post(url, json={"text": text})
        times.append(time.time() - start)
    avg_time = sum(times) / len(times)
    print("{} average inference time over 100 runs: {:.4f} seconds".format(name, avg_time))

test_service("http://localhost:8001/infer", "Torch Inference")
test_service("http://localhost:8002/infer", "ONNX Inference")
