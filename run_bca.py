import threading
import cv2
from core.main import main, app

class_name = "bca"

def run_flask():
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    try:
        main(class_name)
    except KeyboardInterrupt:
        print("\n❌ System interrupted. Exiting gracefully...")
        cv2.destroyAllWindows()