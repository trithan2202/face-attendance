from camera.worker import RecognitionWorker


def main():
    worker = RecognitionWorker(
        camera_source=0,
        cooldown_seconds=10,
        min_checkout_minutes=1 # Test tạm sửa lại 1 phút, để ban đầu là 60p
    )

    worker.run()


if __name__ == "__main__":
    main()