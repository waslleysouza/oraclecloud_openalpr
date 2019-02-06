#!/usr/bin/python3
# Waslley Souza (waslleys@gmail.com)
# 2018

import cv2
import sys
import imutils
import time
import multiprocessing
import os
import platform
import json
from argparse import ArgumentParser
from imutils.video import VideoStream
from oraclecloud import Iot, Storage

with open("deployment.json", 'r') as f:
    datastore = json.load(f)

os.environ['PATH'] = datastore["ALPR_DIR"] + ';' + os.environ['PATH']
from openalpr import Alpr


IOT_USER = datastore["IOT_USER"]
IOT_PASS = datastore["IOT_PASS"]
IOT_URL = datastore["IOT_URL"]
IOT_SHARED_SECRET = datastore["IOT_SHARED_SECRET"]
IOT_DEVICE_MODEL_URN = datastore["IOT_DEVICE_MODEL_URN"]
IOT_DEVICE_MODEL_FORMAT_URN = IOT_DEVICE_MODEL_URN + ":message"

STORAGE_USER = datastore["STORAGE_USER"]
STORAGE_PASS = datastore["STORAGE_PASS"]
STORAGE_IDENTITY = datastore["STORAGE_IDENTITY"]

FRAME_SKIP = datastore["FRAME_SKIP"]
country = datastore["COUNTRY"]
config = "openalpr.conf"
runtime_data = "runtime_data/"


def main():
    try:
        print("Starting...")
        alpr = Alpr(country, config, runtime_data)
        
        if not alpr.is_loaded():
            print("Error loading OpenALPR")
        else:
            print("Using OpenALPR " + alpr.get_version())

            alpr.set_top_n(1)
            alpr.set_detect_region(False)

            # initialize the video stream and allow the cammera sensor to warmup
            video_source = (0 if options["videosource"] == None else options["videosource"])
            vs = VideoStream(usePiCamera=options["picamera"] > 0, src=video_source).start()
            time.sleep(2.0)
            _frame_number = 0
            print("Running...")

            # loop over the frames from the video stream
            while True:
                frame = vs.read()
                #frame = imutils.resize(frame)
                #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                _frame_number += 1
                if _frame_number % FRAME_SKIP == 0:
                    frame_array = (cv2.imencode(".jpg", frame)[1]).tostring()
                    results = alpr.recognize_array(frame_array)
                    if len(results["results"]) > 0:
                        pool.apply_async(_validate, args=[frame_array, results, device, iot, storage])
                                
                if options["imshow"]:
                    # show the frame
                    cv2.imshow("Frame", frame)
                
                key = cv2.waitKey(1) & 0xFF
                # if the `q` key was pressed, break from the loop
                if key == ord("q"):
                    break

    except:
        print("[main] Unexpected error:", sys.exc_info())

    finally:
        if alpr:
            alpr.unload()
    
        pool.close()
        cv2.destroyAllWindows()
        vs.stop()


def _validate(frame, results, device, iot, storage):
    try:
        for i, plate in enumerate(results["results"]):
            best_candidate = plate["candidates"][0]
            if best_candidate["confidence"] > 80 and best_candidate["matches_template"] > 0:
                print("Plate #{}: {:7s} ({:.2f}%)".format(i, best_candidate["plate"].upper(), best_candidate["confidence"]))
                #path = iot.createStorageObject("iot-image", device["name"] + "_" + best_candidate["plate"].upper() + ".jpg", frame)
                #storage.create_or_replace_object("iot-image", device["name"] + "_" + best_candidate["plate"].upper() + ".jpg", frame)
                path = datastore["STORAGE_PATH"] + device["name"] + "_" + best_candidate["plate"].upper() + ".jpg"
                data = {
                    "license_plate": best_candidate["plate"].upper(),
                    "confidence": best_candidate["confidence"],
                    "picture": path
                }
                iot.send_message(device, "urn:com:oracle:iot:device:camera:message", data)

    except:
        print("[_validate] Unexpected error:", sys.exc_info())


def _open_file(file_name):
    f = open(file_name, 'r')
    text = f.read()
    f.close()
    return text


def _create_file(file_name, text):
    f = open(file_name, 'w')
    f.write(text)
    f.close()


if __name__ == "__main__":
    parser = ArgumentParser(description="OpenALPR Python Program")
    parser.add_argument("-p", "--picamera", type=int, default=-1, help="whether or not the Raspberry Pi camera should be used")
    parser.add_argument("-v", "--videosource", type=str, help="URL that should be used")
    parser.add_argument("-s", "--imshow", default=False, help="Show image/video")
    options = vars(parser.parse_args())
    
    storage = Storage(STORAGE_USER, STORAGE_PASS, STORAGE_IDENTITY)
    iot = Iot(IOT_USER, IOT_PASS, IOT_URL, False)

    if os.path.isfile("device.txt"):
        device_id = _open_file('device.txt')
        device = iot.get_device(device_id)  
        iot.set_shared_secret(IOT_SHARED_SECRET)

    else:
        device_model = iot.get_device_model(IOT_DEVICE_MODEL_URN)
        if not device_model:
            formats = json.loads(_open_file('formats.json'))
            device_model = iot.create_device_model("Camera", IOT_DEVICE_MODEL_URN, formats)

        device_name = platform.node() + "_Camera"
        device = iot.create_device(device_name, IOT_SHARED_SECRET, hardware_id=device_name)
        iot.activate_device(device, device_model["urn"])
        _create_file('device.txt', device['id'])

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    main()