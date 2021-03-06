# coding=utf-8
import getpass
import re
import requests
import subprocess


BASE_URL = 'https://api.humppakone.com/'


class InvalidLogin(Exception):
    pass


class Song:
    def __init__(self, data):
        self.api_url = data['url']
        self.id = data['id']
        self.mp3_url = data['download_url']
        self.filename = data['filename']
        self.title = re.sub(r'^.*/', '', self.filename)


class Player:
    def __init__(self):
        self.token = None
        self.current_song = None
        self.autoplay = False
        while not self.token:
            username, password = self.prompt_login()
            try:
                self.token = self.get_auth_token(username, password)
            except InvalidLogin:
                print('Login Failed')

        self.load_random_song()
        while True:
            print("\033[H\033[J")
            print('Next: {}'.format(self.current_song.title))
            command = input('[P]lay / [N]ext / [S]earch / [Q]uit')
            if command.lower() == 'p':
                self.play()
            elif command.lower() == 'n':
                self.load_random_song()
                continue
            elif command.lower() == 's':
                self.prompt_search()
            elif command.lower() == 'q':
                break

    def prompt_search(self):
        print("\033[H\033[J")
        search_terms = input('Search: ')
        r = requests.get(
            '{}songs/?q={}'.format(BASE_URL, search_terms),
            headers={
                'Authorization': 'TOKEN {}'.format(self.token)
            }
        )
        results = [Song(s)for s in r.json()]
        if len(results) == 0:
            print('No results')
            return
        for i, song in enumerate(results):
            print('{}. {}'.format(i+1, song.title))

        n = input('Enter search result number')
        try:
            k = int(n)
            self.current_song = results[k-1]
            self.play()
        except(ValueError, IndexError):
            pass

    def play(self):
        print("\033[H\033[J")
        print('Playing: {}'.format(self.current_song.title))
        full_mp3_url = '{}.mp3?auth_token={}'.format(
            self.current_song.mp3_url,
            self.token
        )
        mpv_process = subprocess.Popen(
            [
                'mpv',
                full_mp3_url,
                '--quiet',
                '--no-video',
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        quit = False
        while True:
            try:
                nextline = mpv_process.stdout.readline()
                if nextline == '' and mpv_process.poll() is not None:
                    break
            except KeyboardInterrupt:
                quit = True
                mpv_process.kill()
                break

        self.load_random_song()
        if not quit:
            self.play()


    def prompt_login(self):
        username = input("Username (%s): " % getpass.getuser())
        if not username:
            username = getpass.getuser()
        password = getpass.getpass()
        return username, password

    def get_auth_token(self, username, password):
        r = requests.post(
            '{}login'.format(BASE_URL),
            data={'username': username,
                  'password': password}
        )
        if r.status_code != 200:
            raise InvalidLogin()
        return r.json().get('token')

    def load_random_song(self):
        r = requests.get(
            '{}songs/random/'.format(BASE_URL),
            headers={
                'Authorization': 'TOKEN {}'.format(self.token)
            }
        )
        if r.status_code == 200:
            self.current_song = Song(r.json())


def main():
    Player()


if __name__ == '__main__':
    main()
