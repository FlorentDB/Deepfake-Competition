from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

import time
import sys
import os
import shutil

from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.common.exceptions import NoSuchElementException
import pytube
from tqdm import tqdm
from typing import List, Tuple


def get_all_videos(
    url: str,
    wait_time_s: int = 5,
    headless: bool = True,
) -> List[Tuple[str, str]]:
    firefox_options = Options()
    if headless:
        firefox_options.add_argument("-headless")
    driver = webdriver.Firefox(
        service=FirefoxService(GeckoDriverManager().install()),
        options=firefox_options,
        )  
    driver.get(url)
    time.sleep(20)
    # do it manually
    # button = driver.find_element(By.XPATH, "//button[0]")
    # button = driver.find_element(By.XPATH, '//button[contains(.,"Reject")]')
    # driver.execute_script("arguments[0].click();", button)

    last_height = driver.execute_script("return document.documentElement.scrollHeight")

    # counter = low-1

    tic = time.time()
    while True:
        
        # Scroll to the bottom of page
        driver.execute_script("window.scrollTo(0, arguments[0]);", last_height)
        # Wait for new videos to show up
        time.sleep(wait_time_s)

        # Calculate new document height and compare it with last height
        new_height = driver.execute_script(
            "return document.documentElement.scrollHeight"
        )
        if new_height == last_height:
            break
        last_height = new_height
        print("scrolling ...")

    links = driver.find_elements(By.ID, "video-title-link")
    links = [(x.text, x.get_attribute("href")) for x in links]
    print(f'Elapsed time : {(time.time()-tic):.2f} sec')
    return links


def url_channel_to_file(
    filename: str,
    url: str,
    headless: bool = True,
) -> List[Tuple[str, str]]:
    """
    Save links in a text file following the scheme:

    TITLE : VIDEO1
    https://...
    TITLE : VIDEO2
    https://...
    [...]

    """
    f = open(filename, "w+")
    lines = get_all_videos(url, headless=headless)
    for l in lines:
        title, link = l
        title = str(title)
        link = str(link)

        f.write("TITLE : " + title + "\n")
        f.write(link + "\n")

    f.close()
    return lines


def read_channel_file(filename: str, low: int, high: int) -> List[str]:
    lines = open(filename, 'r').readlines()
    links = []
    print(f'low = {low}, high = {high}')

    nocounter = low == 0 or high == 0
    counter = low-1
    for line in lines:
        if line.startswith("https:"):
            counter += 1
            links.append(line)
            if counter == high and not nocounter:
                break
    print(links)
    return links


def download_list(l: str, outdir: str = ".", extract_audio: bool = False, verbose: bool = True, overwrite: bool = True):
    outdirvideos = os.path.join(outdir, 'videos')
    outdirsaudios = os.path.join(outdir, 'audios')
    os.makedirs(outdirvideos, exist_ok=True)
    os.makedirs(outdirsaudios, exist_ok=True)
    tic = time.time()
    for url in tqdm(l):
        try:
            v = pytube.YouTube(url)  #  Don't use that : , use_oauth=True, allow_oauth_cache=True)
            filename = eval("'" + v.streams.filter(file_extension='mp4').get_highest_resolution().default_filename + "'")
            video_filepath = os.path.join(outdirvideos, filename)
            if os.path.exists(video_filepath) and not overwrite:
                continue            
            v.streams.filter(file_extension='mp4').get_highest_resolution().download(output_path=outdirvideos)
            # v.streams.filter(file_extension='mp4').order_by("abr").last().download(output_path=outdir)
            if verbose:
                print(f"Downloaded {url}, file {v.title} ")

            print(video_filepath)
            audio_filepath = os.path.join(outdirsaudios, filename.replace('.mp4', '.mp3'))
            
            if extract_audio:
                print('extract audio')
                cmd = 'ffmpeg -i ' + video_filepath + ' -map 0:a -ac 2 ' + audio_filepath
                print(cmd)
                out = os.system(cmd)
                if out == 0:
                    print('audio extraction = success')
            if verbose:
                print(f"Downloaded {url} ")
        except Exception as error:
            print(f"Download {url} failed, skipping ...")
            print(f"An error occurred: {error}")
            continue
    print(f'Elapsed time : {(time.time()-tic):.2f} sec')

def config_parser():

    import argparse

    parser = argparse.ArgumentParser('\n\n1) python yt_channel.py --url https://www.youtube.com/@EmmanuelMacron/videos --getlist  --outputdir /mnt/ddr/data/Macron --listfilename EMlist.txt\n\n2) python yt_channel.py --url https://www.youtube.com/@EmmanuelMacron/videos --download --outputdir /mnt/ddr/data/Macron --listfilename EMlist.txt\n')
    parser.add_argument('--url', type=str, required=False, help='Youtube channel url')
    # parser.add_argument('--list', action='store_true', required=True, help='list filename')    
    parser.add_argument('--getlist', action='store_true', required=False, help='get file list')
    parser.add_argument('--download', action='store_true', help='download file list')
    parser.add_argument('--nooverwrite', action='store_true', help='do not overwrite existing videos/audios if True')
    parser.add_argument('--listfilename', type=str, required=True, help='file containing youtube video urls')
    parser.add_argument('--low', type=int, required=False, default=0, help='first Youtube url to be downloaded in the file list or on-the-fly list')
    parser.add_argument('--high', type=int, required=False, default= 0, help='last Youtube url to be downloaded in ...\n(if low is 1 and high is 10 the download 10 videos)')
    parser.add_argument('--outputdir', type=str, default='./output', help='store list and Youtube videos')
    parser.add_argument('--audio', action='store_true', help='convert video to audio')
    parser.add_argument('--headless', action='store_true', help='do not show web scraping if True')

    return parser


if __name__ == "__main__":

    parser = config_parser()
    args = parser.parse_args()


    url = args.url   # "https://www.youtube.com/@julsaintjean/videos"

    filename = args.listfilename  # "jul.txt"
    links_dir = os.path.join(args.outputdir, 'links')
    os.makedirs(links_dir, exist_ok=True)   
    links_file = os.path.join(links_dir, filename)
     
    if not os.path.exists(links_file) and not args.getlist:
        sys.exit('no list provided nor create list option')
  
    if args.getlist:
        print('get full file list and put it to file')
        # web scraping
        url_channel_to_file(links_file, url, headless=args.headless)
      
    if args.download:
        print('read file list')
        if args.low > args.high and not (args.low == 0 and args.high == 0):
            sys.exit('set low and high lines for list correctly : high >= low > 0')
        if not os.path.exists(links_file):
            sys.exit('no list file provided')
        # read file list
        links = read_channel_file(links_file, args.low, args.high)
        print('download list')         
        download_list(links, outdir=args.outputdir, overwrite=not args.nooverwrite)
        print('done')
