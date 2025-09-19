from flask import request
import json
import hashlib
import time
import asyncio
class sans:
    def __init__(self, sansurl, app, loop=None):
        self.registeredfuncs = {}
        self.sansurl = sansurl
        self.app = app
        self.loop = loop
        self.app.route("/gameupdates", methods=["POST"])(self.gameupdates)
        self.app.route("/gameupdates/", methods=["POST"])(self.gameupdates)
    def registercallback(self,function,gameid):
        self.registeredfuncs[gameid] = function
    def removecallback(self,gameid):
        del self.registeredfuncs[gameid]

    def createchallenge(self, maxtries=-1):
        gameid = int(time.time()*10)
        triesleft = [maxtries]
        queue = asyncio.Queue()

        async def callback(data, received_gameid):
            await queue.put(data)
            if triesleft[0] > 0:
                triesleft[0] -= 1

        self.registercallback(callback, gameid)
        print(f"Challenge created with gameid: {gameid}")

        async def challenge_generator():
            # First yield the URL
            yield f"{self.sansurl}?i={gameid}"

            # Then yield game data as it comes in
            while triesleft[0]:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=100.0)
                    pause = yield data
                    if pause == "pause": break
                except asyncio.TimeoutError:
                    continue

        return challenge_generator()
    def gameupdates(self):
        print(request)
        print(json.dumps(dict(request.form),indent=4))
        response = dict(request.form)

        gameid = response.get('gameid', '')
        mode = response.get('mode', '')
        condition = response.get('condition', '')
        timestamp = response.get('timestamp', '')
        received_hash = response.get('hash', '')

        # Compute expected hash: gameid + timestamp + condition + "e" + mode + "w"
        hash_string = gameid + timestamp + condition + "e" + mode + "w"
        computed_hash = hashlib.md5(hash_string.encode()).hexdigest()
        # print("mew",int(float(timestamp)+1))
        # print("miav", int(float(timestamp)+1)%937)
        print(f"Hash string: '{hash_string}'")
        print(f"Computed: {computed_hash}")
        print(f"Received: {received_hash}")
        print("valid?",computed_hash == received_hash , not int(float(timestamp)+1)%937)
        for idforgame,func in self.registeredfuncs.items():
            if str(idforgame) == str(gameid):
                if self.loop:
                    asyncio.run_coroutine_threadsafe(func({**response,"valid":computed_hash == received_hash and not int(float(timestamp)+1)%937},gameid), self.loop)
                else:
                    asyncio.create_task(func({**response,"valid":computed_hash == received_hash and not int(float(timestamp)+1)%937},gameid))
            
        return {"message":"ok"}