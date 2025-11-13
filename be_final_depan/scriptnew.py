import requests
import cv2
import os
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
TEMP_DIR = "temp_images"

# Pastikan direktori temporary ada
os.makedirs(TEMP_DIR, exist_ok=True)

def clear_screen():
    """Membersihkan layar terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Menampilkan header menu"""
    print("\n" + "="*50)
    print(f"  {title}")
    print("="*50 + "\n")

def get_all_owners():
    """Mengambil data semua owner dari API"""
    try:
        response = requests.get(f"{BASE_URL}/users/userowner/")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: Gagal mengambil data owner (Status: {response.status_code})")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def check_user_images(username):
    """Cek apakah user sudah memiliki gambar training"""
    try:
        response = requests.get(
            f"{BASE_URL}/face/getuserimageexists/",
            params={"username": username}
        )
        return response.status_code, response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None, None

def verify_face_with_haar(image_path):
    """Verifikasi apakah ada wajah dalam gambar menggunakan Haar Cascade"""
    try:
        # Load Haar Cascade classifier
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

        # Baca gambar
        img = cv2.imread(image_path)
        if img is None:
            return False

        # Convert ke grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Deteksi wajah
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        return len(faces) > 0
    except Exception as e:
        print(f"Error verifikasi wajah: {e}")
        return False

def auto_capture_images(username, num_images):
    """Mengambil gambar secara otomatis dan verifikasi wajah"""
    cap = cv2.VideoCapture(1, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("❌ Tidak bisa membuka kamera index 1, mencoba index 2...")
        cap = cv2.VideoCapture(2, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("❌ Tidak ada kamera yang bisa dibuka. Periksa device /dev/video*.")
        exit()
    cv2.namedWindow('Kamera', cv2.WINDOW_NORMAL)
    # Load Haar Cascade
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    verified_images = []
    user_temp_dir = os.path.join(TEMP_DIR, username)
    os.makedirs(user_temp_dir, exist_ok=True)

    print(f"\nMemulai pengambilan {num_images} gambar untuk user: {username}")
    print("Proses pengambilan gambar otomatis dimulai...")
    print("Tekan ESC untuk membatalkan\n")

    captured_count = 0
    frame_count = 0
    capture_interval = 30  # Ambil gambar setiap 30 frame (sekitar 1 detik)

    while len(verified_images) < num_images:
        ret, frame = cap.read()
        if not ret:
            print("Error: Tidak dapat membaca frame dari webcam")
            break

        frame_count += 1

        # Deteksi wajah untuk preview
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Gambar rectangle pada wajah yang terdeteksi
        # for (x, y, w, h) in faces:
        #     cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        #
        # # Tampilkan info
        # cv2.putText(frame, f"Terverifikasi: {len(verified_images)}/{num_images}", (10, 30),
        #             cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        # cv2.putText(frame, f"Total Captured: {captured_count}", (10, 70),
        #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        # cv2.putText(frame, "ESC: Batal", (10, 110),
        #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow('Auto Capture Images', frame)

        # Ambil gambar otomatis setiap interval tertentu
        if frame_count >= capture_interval and len(faces) > 0:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{username}_{captured_count+1}_{timestamp}.jpg"
            filepath = os.path.join(user_temp_dir, filename)

            cv2.imwrite(filepath, frame)
            captured_count += 1

            # Verifikasi wajah
            if verify_face_with_haar(filepath):
                verified_images.append(filepath)
                print(f"✓ Gambar {len(verified_images)} berhasil diambil dan diverifikasi (Total captured: {captured_count})")
            else:
                os.remove(filepath)
                print(f"✗ Gambar {captured_count} gagal verifikasi, dihapus (Terverifikasi: {len(verified_images)}/{num_images})")

            frame_count = 0  # Reset counter

        # Check untuk ESC key
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            print("\n⚠ Pengambilan gambar dibatalkan oleh user")
            cap.release()
            cv2.destroyAllWindows()
            return []

    cap.release()
    cv2.destroyAllWindows()

    print(f"\n✓ Selesai! Total gambar terverifikasi: {len(verified_images)}")
    return verified_images

def upload_images_to_server(username, image_paths):
    """Upload gambar ke server"""
    try:
        files = []
        for img_path in image_paths:
            files.append(
                ('image_list', (os.path.basename(img_path), open(img_path, 'rb'), 'image/jpeg'))
            )

        data = {'username': username}

        response = requests.post(
            f"{BASE_URL}/face/createimagetrainingusernew/",
            data=data,
            files=files
        )

        # Tutup semua file
        for _, (_, file_obj, _) in files:
            file_obj.close()

        return response.status_code, response.json()
    except Exception as e:
        print(f"Error upload: {e}")
        return None, None

def cleanup_temp_files(username):
    """Membersihkan file temporary"""
    user_temp_dir = os.path.join(TEMP_DIR, username)
    if os.path.exists(user_temp_dir):
        for file in os.listdir(user_temp_dir):
            os.remove(os.path.join(user_temp_dir, file))
        os.rmdir(user_temp_dir)

def process_user_registration(username):
    """Proses registrasi gambar untuk user"""
    # Cek apakah user sudah punya gambar
    status_code, response = check_user_images(username)

    if status_code == 200:
        print("\n✓ Gambar user sudah ditemukan!")
        print(f"Jumlah gambar: {len(response['data'])} gambar")
        print("\nSilahkan pilih pilihan berikutnya")
        input("\nTekan Enter untuk kembali ke menu utama...")
        return True  # Return True untuk signal kembali ke menu utama
    elif status_code == 403:
        print("\n⚠ Gambar user tidak ditemukan, perlu mendaftar gambar baru")

        # Input jumlah gambar
        while True:
            try:
                num_images = int(input("\nMasukkan jumlah gambar yang akan diambil: "))
                if num_images > 0:
                    break
                else:
                    print("Jumlah harus lebih dari 0!")
            except ValueError:
                print("Input tidak valid, masukkan angka!")

        # Proses pengambilan gambar otomatis dengan loop sampai cukup
        verified_images = []
        attempt = 1

        while len(verified_images) < num_images:
            remaining = num_images - len(verified_images)

            if attempt > 1:
                print(f"\n⚠ Gambar terverifikasi masih kurang {remaining} gambar")
                print(f"Melanjutkan pengambilan gambar (Percobaan ke-{attempt})...")
                time.sleep(2)

            print(f"\n--- Pengambilan Batch {attempt}: Target {remaining} gambar ---")
            captured = auto_capture_images(username, remaining)

            if not captured:
                print("\n⚠ Pengambilan gambar dibatalkan")
                cleanup_temp_files(username)
                input("Tekan Enter untuk kembali ke menu utama...")
                return False  # Return False untuk tetap di menu username

            verified_images.extend(captured)
            attempt += 1

            # Batasi percobaan maksimal
            if attempt > 10:
                print("\n✗ Terlalu banyak percobaan. Proses dibatalkan.")
                cleanup_temp_files(username)
                input("Tekan Enter untuk kembali ke menu utama...")
                return False  # Return False untuk tetap di menu username

        print(f"\n{'='*50}")
        print(f"✓ SUKSES! Berhasil mengumpulkan {len(verified_images)} gambar terverifikasi")
        print(f"{'='*50}")

        # Upload ke server
        print("\n⏳ Mengupload gambar ke server...")
        status_code, response = upload_images_to_server(username, verified_images)

        if status_code == 200:
            print("\n" + "="*50)
            print("✓ BERHASIL MENGUNGGAH GAMBAR KE SERVER!")
            print("="*50)
            print(f"Message: {response.get('message', '')}")
            print(f"Jumlah gambar terupload: {len(response.get('data', []))}")
        else:
            print(f"\n✗ Gagal mengunggah gambar (Status: {status_code})")
            print(f"Response: {response}")

        # Cleanup
        cleanup_temp_files(username)
        input("\nTekan Enter untuk kembali ke menu utama...")
        return True  # Return True untuk signal kembali ke menu utama
    else:
        print(f"\n✗ Error saat cek gambar user (Status: {status_code})")
        input("Tekan Enter untuk kembali ke menu utama...")
        return False  # Return False untuk tetap di menu username
def menu_pilih_owner():
    """Menu untuk memilih owner"""
    while True:
        clear_screen()
        print_header("PILIH USER OWNER")

        owners = get_all_owners()
        if not owners:
            print("Tidak ada data owner atau gagal mengambil data")
            input("\nTekan Enter untuk kembali...")
            return

        # Tampilkan daftar owner
        for idx, owner in enumerate(owners, 1):
            print(f"{idx}. {owner['username']} ({owner['email']})")
        print(f"{len(owners)+1}. Kembali ke menu utama")

        try:
            choice = int(input("\nPilih user (masukkan nomor): "))
            if 1 <= choice <= len(owners):
                selected_owner = owners[choice-1]
                result = process_user_registration(selected_owner['username'])

                # Jika result True, kembali ke menu utama
                if result:
                    break
                # Jika result False atau None, tetap di loop menu username

            elif choice == len(owners)+1:
                break
            else:
                print("Pilihan tidak valid!")
                time.sleep(1)
        except ValueError:
            print("Input tidak valid!")
            time.sleep(1)

def process_additional_registration(username):
    """Proses registrasi gambar tambahan untuk user yang sudah ada"""
    # Cek apakah user sudah punya gambar
    status_code, response = check_user_images(username)

    if status_code == 403:
        print("\n✗ Gambar user tidak ditemukan dalam database!")
        print("User ini belum memiliki gambar training.")
        print("Silahkan gunakan menu 'Registrasi Gambar User Owner' terlebih dahulu.")
        input("\nTekan Enter untuk kembali ke menu utama...")
        return True  # Return True untuk kembali ke menu utama
    elif status_code == 200:
        print("\n✓ Gambar user ditemukan dalam database!")
        print(f"Jumlah gambar saat ini: {len(response['data'])} gambar")
        print("\nMelanjutkan proses penambahan gambar...")

        # Input jumlah gambar tambahan
        while True:
            try:
                num_images = int(input("\nMasukkan jumlah gambar tambahan yang akan diambil: "))
                if num_images > 0:
                    break
                else:
                    print("Jumlah harus lebih dari 0!")
            except ValueError:
                print("Input tidak valid, masukkan angka!")

        # Proses pengambilan gambar otomatis dengan loop sampai cukup
        verified_images = []
        attempt = 1

        while len(verified_images) < num_images:
            remaining = num_images - len(verified_images)

            if attempt > 1:
                print(f"\n⚠ Gambar terverifikasi masih kurang {remaining} gambar")
                print(f"Melanjutkan pengambilan gambar (Percobaan ke-{attempt})...")
                time.sleep(2)

            print(f"\n--- Pengambilan Batch {attempt}: Target {remaining} gambar ---")
            captured = auto_capture_images(username, remaining)

            if not captured:
                print("\n⚠ Pengambilan gambar dibatalkan")
                cleanup_temp_files(username)
                input("Tekan Enter untuk kembali ke menu utama...")
                return False  # Return False untuk tetap di menu username

            verified_images.extend(captured)
            attempt += 1

            # Batasi percobaan maksimal
            if attempt > 10:
                print("\n✗ Terlalu banyak percobaan. Proses dibatalkan.")
                cleanup_temp_files(username)
                input("Tekan Enter untuk kembali ke menu utama...")
                return False  # Return False untuk tetap di menu username

        print(f"\n{'='*50}")
        print(f"✓ SUKSES! Berhasil mengumpulkan {len(verified_images)} gambar tambahan terverifikasi")
        print(f"{'='*50}")

        # Upload ke server
        print("\n⏳ Mengupload gambar ke server...")
        status_code, response = upload_images_to_server(username, verified_images)

        if status_code == 200:
            print("\n" + "="*50)
            print("✓ BERHASIL MENGUNGGAH GAMBAR TAMBAHAN KE SERVER!")
            print("="*50)
            print(f"Message: {response.get('message', '')}")
            print(f"Jumlah gambar terupload: {len(response.get('data', []))}")
        else:
            print(f"\n✗ Gagal mengunggah gambar (Status: {status_code})")
            print(f"Response: {response}")

        # Cleanup
        cleanup_temp_files(username)
        input("\nTekan Enter untuk kembali ke menu utama...")
        return True  # Return True untuk signal kembali ke menu utama
    else:
        print(f"\n✗ Error saat cek gambar user (Status: {status_code})")
        input("Tekan Enter untuk kembali ke menu utama...")
        return False  # Return False untuk tetap di menu username

def menu_pilih_owner_additional():
    """Menu untuk memilih owner untuk registrasi gambar tambahan"""
    while True:
        clear_screen()
        print_header("TAMBAH GAMBAR USER OWNER (USER SUDAH ADA)")

        owners = get_all_owners()
        if not owners:
            print("Tidak ada data owner atau gagal mengambil data")
            input("\nTekan Enter untuk kembali...")
            return

        # Tampilkan daftar owner
        for idx, owner in enumerate(owners, 1):
            print(f"{idx}. {owner['username']} ({owner['email']})")
        print(f"{len(owners)+1}. Kembali ke menu utama")

        try:
            choice = int(input("\nPilih user (masukkan nomor): "))
            if 1 <= choice <= len(owners):
                selected_owner = owners[choice-1]
                result = process_additional_registration(selected_owner['username'])

                # Jika result True, kembali ke menu utama
                if result:
                    break
                # Jika result False atau None, tetap di loop menu username

            elif choice == len(owners)+1:
                break
            else:
                print("Pilihan tidak valid!")
                time.sleep(1)
        except ValueError:
            print("Input tidak valid!")
            time.sleep(1)

def capture_single_image_with_verification(max_attempts=10):
    """Mengambil satu gambar dan verifikasi wajah dengan retry otomatis"""
    cap = cv2.VideoCapture(1, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("❌ Tidak bisa membuka kamera index 1, mencoba index 2...")
        cap = cv2.VideoCapture(2, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("❌ Tidak ada kamera yang bisa dibuka. Periksa device /dev/video*.")
        return None

    cv2.namedWindow('Face Verification', cv2.WINDOW_NORMAL)

    # Load Haar Cascade
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    log_temp_dir = os.path.join(TEMP_DIR, "face_log")
    os.makedirs(log_temp_dir, exist_ok=True)

    print("\n⏳ Memulai pengambilan gambar untuk verifikasi wajah...")
    print("Tekan ESC untuk membatalkan\n")

    attempt = 0
    verified_image = None

    while attempt < max_attempts and verified_image is None:
        attempt += 1
        print(f"\n--- Percobaan ke-{attempt} ---")

        frame_count = 0
        capture_delay = 60  # Delay 60 frame (~2 detik) untuk stabilisasi

        while frame_count < capture_delay:
            ret, frame = cap.read()
            if not ret:
                print("Error: Tidak dapat membaca frame dari webcam")
                break

            frame_count += 1

            # Deteksi wajah untuk preview
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            # Gambar rectangle pada wajah yang terdeteksi
            # for (x, y, w, h) in faces:
            #     cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            #
            # # Tampilkan info
            # cv2.putText(frame, f"Percobaan: {attempt}/{max_attempts}", (10, 30),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            # cv2.putText(frame, "Posisikan wajah di tengah", (10, 60),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            # cv2.putText(frame, "ESC: Batal", (10, 90),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow('Face Verification', frame)

            # Check untuk ESC key
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print("\n⚠ Verifikasi wajah dibatalkan oleh user")
                cap.release()
                cv2.destroyAllWindows()
                return None

        # Ambil frame terakhir untuk capture
        ret, frame = cap.read()
        if not ret:
            print("Error: Tidak dapat membaca frame untuk capture")
            continue

        # Simpan gambar sementara
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"face_log_{timestamp}.jpg"
        filepath = os.path.join(log_temp_dir, filename)

        cv2.imwrite(filepath, frame)
        print(f"📸 Gambar diambil: {filename}")

        # Verifikasi wajah
        if verify_face_with_haar(filepath):
            verified_image = filepath
            print(f"✓ Wajah terdeteksi! Gambar terverifikasi.")
        else:
            os.remove(filepath)
            print(f"✗ Wajah tidak terdeteksi, mengambil ulang...")

            if attempt < max_attempts:
                print(f"⏳ Menunggu 2 detik sebelum percobaan berikutnya...")
                time.sleep(2)

    cap.release()
    cv2.destroyAllWindows()

    if verified_image:
        print(f"\n✓ Berhasil! Gambar wajah terverifikasi: {os.path.basename(verified_image)}")
    else:
        print(f"\n✗ Gagal memverifikasi wajah setelah {max_attempts} percobaan")

    return verified_image

def send_face_log_to_server(image_path):
    """Mengirim gambar face log ke server untuk verifikasi"""
    try:
        files = [
            ('image', (os.path.basename(image_path), open(image_path, 'rb'), 'image/jpeg'))
        ]

        print("\n⏳ Mengirim gambar ke server untuk verifikasi...")
        response = requests.post(
            f"{BASE_URL}/face/createlogusersmartnew/",
            files=files
        )

        # Tutup file
        files[0][1][1].close()

        return response.status_code, response.json()
    except Exception as e:
        print(f"Error saat mengirim ke server: {e}")
        return None, None

def cleanup_face_log_temp():
    """Membersihkan file temporary face log"""
    log_temp_dir = os.path.join(TEMP_DIR, "face_log")
    if os.path.exists(log_temp_dir):
        for file in os.listdir(log_temp_dir):
            file_path = os.path.join(log_temp_dir, file)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error menghapus file {file}: {e}")
        try:
            os.rmdir(log_temp_dir)
        except Exception as e:
            print(f"Error menghapus direktori: {e}")

def process_face_log_verification():
    """Proses verifikasi wajah untuk log user"""
    clear_screen()
    print_header("VERIFIKASI WAJAH USER (FACE LOG)")

    print("Sistem akan mengambil satu gambar wajah Anda untuk verifikasi.")
    print("Pastikan wajah Anda terlihat jelas di kamera.\n")

    input("Tekan Enter untuk memulai...")

    # Ambil gambar dengan verifikasi
    verified_image = capture_single_image_with_verification(max_attempts=10)

    if not verified_image:
        print("\n✗ Proses verifikasi wajah gagal atau dibatalkan")
        cleanup_face_log_temp()
        input("\nTekan Enter untuk kembali ke menu utama...")
        return

    # Kirim ke server
    status_code, response = send_face_log_to_server(verified_image)

    if status_code == 200 and response:
        print("\n" + "="*60)
        print("✓ VERIFIKASI BERHASIL!")
        print("="*60)

        # Parse response
        result = response.get('result', [])
        confidence = response.get('confidence', 'N/A')

        if result and len(result) > 0:
            log_data = result[0]
            status = log_data.get('status', 'Unknown')
            log_id = log_data.get('log_id', 'N/A')
            id_face_user = log_data.get('id_face_user', 'N/A')
            access_time = log_data.get('access_time', 'N/A')

            print(f"\n📋 Detail Verifikasi:")
            print(f"   Status         : {status}")
            print(f"   Confidence     : {confidence}")
            print(f"   User ID        : {id_face_user}")
            print(f"   Log ID         : {log_id}")
            print(f"   Waktu Akses    : {access_time}")

            # Tampilkan status dengan warna
            if status.lower() == "authorized":
                print("\n" + "="*60)
                print("✅ STATUS: AUTHORIZED - Akses Diberikan")
                print("="*60)
            else:
                print("\n" + "="*60)
                print("❌ STATUS: UNAUTHORIZED - Akses Ditolak")
                print("="*60)

            # Jeda waktu sebelum kembali ke menu
            print("\n⏳ Kembali ke menu dalam 5 detik...")
            time.sleep(5)
        else:
            print("\n⚠ Data hasil verifikasi tidak lengkap")
            input("\nTekan Enter untuk kembali ke menu utama...")
    else:
        print("\n" + "="*60)
        print(f"✗ VERIFIKASI GAGAL!")
        print("="*60)
        print(f"Status Code: {status_code}")
        print(f"Response: {response}")
        input("\nTekan Enter untuk kembali ke menu utama...")

    # Cleanup
    cleanup_face_log_temp()

def main_menu():
    """Menu utama aplikasi"""
    while True:
        clear_screen()
        print_header("SISTEM REGISTRASI FACE TRAINING")

        print("1. Registrasi Gambar User Owner (User Baru)")
        print("2. Tambah Gambar User Owner (User Sudah Ada)")
        print("3. Verifikasi Wajah User (Face Log)")
        print("4. Keluar")

        choice = input("\nPilih menu: ")

        if choice == "1":
            menu_pilih_owner()
        elif choice == "2":
            menu_pilih_owner_additional()
        elif choice == "3":
            process_face_log_verification()
        elif choice == "4":
            print("\nTerima kasih! Program selesai.")
            break
        else:
            print("Pilihan tidak valid!")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nProgram dihentikan oleh user")
    finally:
        # Cleanup
        if os.path.exists(TEMP_DIR):
            for item in os.listdir(TEMP_DIR):
                item_path = os.path.join(TEMP_DIR, item)
                if os.path.isdir(item_path):
                    try:
                        for file in os.listdir(item_path):
                            os.remove(os.path.join(item_path, file))
                        os.rmdir(item_path)
                    except Exception as e:
                        print(f"Error cleanup {item}: {e}")