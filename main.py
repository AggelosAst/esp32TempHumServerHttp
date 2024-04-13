import asyncio
from flask import Flask, render_template, jsonify, request, send_file
from waitress import serve
from Dependencies.Helper import Helper
import logging
from datetime import datetime
import pytz

logger = logging.getLogger('waitress')

logger.setLevel(logging.INFO)


class Server:
    port = 0
    times: int = 0
    arduino_Data = list([])
    current_arduino_Data = list([])

    app = Flask(__name__, template_folder="WebPages")

    def __init__(self, port: int) -> None:
        self.port = port

    def getconfig(self):
        return self.port

    async def setup(self, helper: Helper) -> None:
        @self.app.route("/arduino", methods=["GET"])
        def ard():
            return render_template("arduinodatadisplay.html")

        @self.app.route("/getarddata", methods=["GET"])
        async def getdata():
            if len(self.current_arduino_Data) < 1:
                return jsonify({
                    "data": []
                })
            else:
                data = self.current_arduino_Data[0]
                hum: int = int(data["hum"])
                temp: int = int(data["temp"])
                hum_indicator: str = ""
                temp_indicator: str = ""
                if hum >= 70:
                    hum_indicator = f"Warning: High humidity detected!"
                elif hum < 30:
                    hum_indicator = f"Warning: Low humidity detected!"
                else:
                    hum_indicator = f"Normal data have been reported."
                if temp > 30:
                    temp_indicator = f"Warning: High temperature detected!"
                elif temp < 10:
                    temp_indicator = f"Warning: Low temperature detected!"
                else:
                    temp_indicator = f"Normal data have been reported."
                return jsonify({
                    "data": self.arduino_Data,
                    "static": self.current_arduino_Data,
                    "static_info": {
                        "hum_info": hum_indicator,
                        "temp_info": temp_indicator
                    }
                })

        @self.app.route("/analysedata", methods=["POST"])
        async def analyse():
            if "prompt" in request.get_json():
                body = request.get_json()
                response: dict
                try:
                    response = await Helper.prompt(
                        f"Youre a AI ChatBot which assists people with analysing tempreture and humidty data. Youre given: Temperature(Celcious), Humidity(Percentage) and a timestamp for each log.  You must use a JSON format to respond, in which you will never use single quotes for json but double quotes:\nYour Response: {self.formatted_help_prompt_for_arduino}\nInformation youre given :\nTemperature: {body['temp']}\nHumidity: {body['hum']}\nTime: {body['time']}\nPrompt: {body['prompt']}")
                    if "error" in response:
                        return jsonify({
                            "error": response["error"]
                        }), 500
                    else:
                        return jsonify({
                            "data": response,
                        })
                except Exception as e:
                    print(e, "Error")
                    return jsonify({
                        "error": e
                    }), 500

        @self.app.route("/api/v1/plotdata", methods=["GET"])
        async def plotdata():
            data: list[dict[str, str, str, str, str, str]] = self.arduino_Data
            hums = list([])
            temps = list([])
            times = list([])
            for metric in data:
                hums.append(metric["hum"])
                temps.append(metric["temp"])
                times.append(metric["time"])
            error: str = helper.plot_data()
            if "Error" in error:
                return jsonify({
                    "error": "File is not ready yet."
                })
            else:
                return send_file("ok.png")

        @self.app.route("/api/v1/data", methods=["POST"])
        async def postdata():
            body = request.get_json()
            if "sensorId" not in body:
                print("Sensor Id missing")
                return jsonify({
                    "error": "Missing sensorId"
                }), 500
            elif "temp" not in body:
                print("Temp missing")
                return jsonify({
                    "error": "Missing temp"
                }), 500
            elif "hum" not in body:
                print("Hum missing")
                return jsonify({
                    "error": "Missing hum"
                }), 500
            else:
                body: dict[str, str] = body
                if helper.last_timestamp is None:
                    helper.last_timestamp = datetime.now(helper.timezone)
                timestamp_difference: dict[str, int] = helper.compare_timestamps(helper.last_timestamp)
                if timestamp_difference["minutes"] == 720:
                    # TODO: Log the data
                    # self.arduino_Data.append({
                    #     "sensorId": body["sensorId"],
                    #     "temp": body["temp"],
                    #     "hum": body["hum"],
                    #     "time": datetime.now(pytz.timezone("Europe/Athens")).strftime("%I:%M %p")
                    # })
                    Helper.save_csv_data({
                        "Temperature": body["temp"],  # temps
                        "Humidity": [body["hum"]],  # hums,
                        "Times": [datetime.now(pytz.timezone("Europe/Athens")).strftime("%I:%M %p")]  # times
                    })
                    helper.last_timestamp = datetime.now(helper.timezone)

                if len(self.current_arduino_Data) < 1:
                    self.current_arduino_Data.append({
                        "sensorId": body["sensorId"],
                        "temp": body["temp"],
                        "hum": body["hum"],
                        "time": datetime.now(pytz.timezone("Europe/Athens")).strftime("%I:%M %p")
                    })
                else:
                    self.current_arduino_Data.pop(0)
                    self.current_arduino_Data.append({
                        "sensorId": body["sensorId"],
                        "temp": body["temp"],
                        "hum": body["hum"],
                        "time": datetime.now(pytz.timezone("Europe/Athens")).strftime("%I:%M %p")
                    })
            return jsonify({
                "data": "Success"
            }), 200

        @self.app.route("/")
        def root():
            return render_template("root.html", description="Fr")

        serve(self.app, host="0.0.0.0", port=self.port, threads=10)


async def startwebserver():
    server = Server(6969)
    await server.setup(Helper())


if __name__ == '__main__':
    asyncio.run(startwebserver())
