import asyncio
import os
import time
import aiohttp
import matplotlib
import matplotlib.pyplot as pl
import pytz
import pandas as pd
from datetime import datetime

matplotlib.use("Agg")


class Helper:
    timezone: pytz.tzinfo = pytz.timezone("Europe/Athens")
    last_timestamp: pytz.tzinfo = None

    @staticmethod
    def clear_csv() -> None:
        if os.path.isfile("data.csv"):
            try:
                os.remove("data.csv")
            except Exception as e:
                print(e)

    @staticmethod
    def plot_data() -> str:
        if not os.path.isfile("data.csv"):
            return "Error"

        # Read in data
        df = pd.read_csv("data.csv", usecols=["Temperature", "Humidity", "Time"])

        # Set up plot
        pl.figure(figsize=(20, 10))
        pl.plot(df["Time"], df["Temperature"], label="Temp", color="red")
        pl.grid()

        # Add title
        pl.title("Temperature Data Per Hours")

        # Label axes
        pl.xlabel("Time")
        pl.ylabel("Temperature (°C)", color="black")

        # Add legend
        pl.legend(loc="upper left")

        # Adjust plot layout
        pl.autoscale(True, "both", False)
        pl.xlim(auto=True)
        pl.ylim(auto=True)
        pl.xticks(rotation=70)
        pl.tight_layout()
        # pl.show()
        if os.path.isfile("ok.png"):
            os.remove("ok.png")
            time.sleep(0.5)
        pl.savefig("ok.png")
        return "Success"

    @classmethod
    def compare_timestamps(cls, ts) -> dict[str, int]:
        timestamp1 = datetime.now(cls.timezone)
        timestamp2 = ts

        timestamp1 = int(timestamp1.timestamp())

        timestamp2 = int(timestamp2.timestamp())

        diff = timestamp1 - timestamp2
        print(f"Difference in minutes is: {int(diff / 60)}")
        # print(f"Difference in seconds is: {int(diff)}")

        return {
            "seconds": int(diff),
            "minutes": int(diff / 60)
        }

    @staticmethod
    def get_timings(data: list[dict[str, str, str, str]]):
        times = list([])
        for metric in data:
            times.append(metric["time"])
        return times

    @staticmethod
    def get_humidity_data(data: list[dict[str, str, str, str]]):
        humidity = list([])
        for metric in data:
            humidity.append(metric["hum"])
        return humidity

    @staticmethod
    def get_temperature_data(data: list[dict[str, str, str, str]]):
        temperature = list([])
        for metric in data:
            temperature.append(metric["temp"])
        return temperature

    @staticmethod
    def save_csv_data(data: dict[str, list[str]]) -> None:
        if os.path.isfile("data.csv"):
            csv_to_save: pd.DataFrame = pd.DataFrame(data)
            csv_to_save.to_csv("data.csv", index=False, header=False, mode="a")
            print("Appended data")
        else:
            df = pd.DataFrame({
                "Temperature": data["Temperature"],
                "Humidity": data["Humidity"],
                "Time": data["Times"]
            })
            df.to_csv("data.csv", header=True, index=False, mode="w")
            print("Initialized data")

    @staticmethod
    def includes(template: str, target: str) -> bool:
        if template.find(target) != -1:
            print("Found")
            return True
        else:
            return False

    @staticmethod
    def includes_in_array(arr: list[dict[str, str]], target: str, property_to_search: str) -> dict:
        element_found = None
        if len(arr) > 0:
            for element in arr:
                if element[property_to_search] == target:
                    element_found = element
                    break
        if element_found is not None:
            return {
                "status": True,
                "element": element_found
            }
        else:
            return {
                "status": False
            }

    @staticmethod
    def remove_item_from_array(array: list[dict[str, str]], target: str, property_to_search: str) -> dict:
        if len(array) > 0:
            for element in array.copy():
                if element[property_to_search] == target:
                    array.remove(element)
                    return {
                        "message": "Removed element",
                        "element": element
                    }

    @staticmethod
    async def prompt(prompt: str):
        data = {"messages": [{"role": "user", "content": prompt}]}
        request: None
        timeout = aiohttp.ClientTimeout(total=3)
        try:
            async with aiohttp.ClientSession(timeout=timeout, headers={"Content-Type": "application/json",
                                                                       "Origin": "https://seoschmiede.at",
                                                                       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; ZumBot/1.0; http://help.zum.com/;WOW64;Trident/7.0;rv:11.0) Chrome/50.0.2661.94 (KHTML, like Gecko)", }) as session:
                async with session.post("https://chatbot-ji1z.onrender.com/chatbot-ji1z", json=data) as response:
                    json_response: dict = {}
                    json_response = await response.json()
                    if "choices" in json_response:
                        print(f"Got a response from AI. Collected in total {len(json_response)}")
                        choices: list[dict[str]] = json_response["choices"]
                        first_choices = choices[0]["message"]["content"]
                        if first_choices is not None:
                            return {
                                "response": first_choices,
                                "status": response.status
                            }
                        else:
                            print("CHOICE IS NONE.")
        except aiohttp.ClientConnectionError as e:
            print("Connection error: ", e)
            return {
                "error": e
            }
        except aiohttp.ClientResponseError as e:
            print("Response error: ", e)
            return {
                "error": e
            }
        except asyncio.TimeoutError:
            print("Request timed out")
            return {
                "error": "Request timeout 3 second total surpassed"
            }
        except Exception as e:
            print("Other error: ", e)
            return {
                "error": e
            }
