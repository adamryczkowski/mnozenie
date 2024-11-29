from gtts import gTTS


def say(text, filename):
    myobj = gTTS(text=text, lang="pl", slow=True)
    myobj.save(filename)


say("ósmy, ułóż, chomiki", "out.mp3")
