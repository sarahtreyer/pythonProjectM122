# coding=utf-8
import json
import urllib
import re
import base64
from fpdf import FPDF
from PIL import Image
from sendgrid import SendGridAPIClient, Attachment, FileName, FileContent, Disposition, FileType
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY='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'


class PDF(FPDF):
    def imagex(self, url, height, width):
        self.image(name=url, x=width, y=height, w=2500 / 80, h=2500 / 80, type='', link=url)

    def imageBackground(self, url, height, width):
        self.image(name=url, x=width, y=height)

    def imageTitel(self, url, height, width):
        self.image(name=url, x=width, y=height, w=4000 / 80)


def addDataToPDF(data, pictureUrls, statistic):
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(0, 0, 230, 330, 'F')
    pdf.set_font('Arial', 'B', 20)
    pdf.set_fill_color(220, 220, 220)
    pdf.imageBackground('logo.png', 25.0, 25.0)
    pdf.imageTitel('logo.png', 15.0, 80.0)
    pdf.set_font('Arial', 'B', 10)
    pdf.rect(10, 40, 190, 131, 'F')

    height = 45.0
    width = 25.0

    # add pictures
    for x in pictureUrls:
        pdf.imagex(x, height, width)
        if width >= 25.0:
            width += 43.0
        if width == 197.0 or width == 369.0:
            width = 25.0
            height += 43.0

    # add text to pictures
    heightText = 80.0
    widthText = 25.0

    for y in data:
        mode = y[2]
        if mode != "Verkauft":
            mode = "zu haben"
        else:
            pdf.set_text_color(79, 121, 66)

        mode = mode + ' (Likes ' + str(y[1]) + ')'
        pdf.text(widthText, heightText, mode)
        if widthText >= 25.0:
            widthText += 43.0
        if widthText == 197.0 or widthText == 369.0:
            widthText = 25.0
            heightText += 43.0
        pdf.set_text_color(0, 0, 0)

    # add text statistic
    pdf.rect(10, 180, 190, 105, 'F')
    pdf.set_font('Arial', 'B', 10)
    text = 'Meiste Likes: ' + str(statistic['abiggestLike'])
    pdf.text(25, 190, text)
    pdf.imagex("images/image" + statistic['abiggestLikeUrl'][-22:] + ".png", 195, 25)

    text = 'Wenigste Likes: ' + str(statistic['alowestLike'])
    pdf.text(75, 190, text)
    pdf.imagex("images/image" + statistic['alowestLikeUrl'][-22:] + ".png", 195, 75)

    text = 'Bester Artikel: ' + str(statistic['aBest']) + ' Likes'
    pdf.text(25, 240, text)
    pdf.imagex("images/image" + statistic['aBestUrl'][-22:] + ".png", 245, 25)

    text = 'Schlechtester Artikel: ' + str(statistic['aWorst']) + ' Likes'
    pdf.text(75, 240, text)
    pdf.imagex("images/image" + statistic['aWorstUrl'][-22:] + ".png", 245, 75)

    textTitel = 'Anzahl verkaufte Artikel: '
    text = str(statistic['aSold']) + ' Artikel'
    pdf.text(140, 190, textTitel)
    pdf.text(140, 195, text)

    textTitel = 'Anzahl nicht verkaufte Artikel: '
    text = str(statistic['aNotSold']) + ' Artikel'
    pdf.text(140, 215, textTitel)
    pdf.text(140, 220, text)

    if statistic['goodWeek'] == 1:
        pdf.set_fill_color(79, 121, 66)
    else:
        pdf.set_fill_color(107, 0, 0)
    text = 'Wochen Status'
    pdf.text(140, 240, text)
    pdf.rect(140, 245, 15, 15, 'F')
    pdf.set_text_color(0, 0, 0)

    pdf.output('instagramReport.pdf', 'F')


# gets all the Data from the API, returns List with Image, Amount of Likes, Title
def getData():
    # WITH URL
    # url = "https://www.instagram.com/vintage.cybernetic/?__a=1"
    # test = urllib.urlopen(url)
    # parsed = json.load(test)

    # WITH TEXT FILE
    with open('api.txt') as jsonFile:
        parsed = json.load(jsonFile)
    nodes = parsed['graphql']['user']['edge_owner_to_timeline_media']['edges']
    result = []

    for key in nodes:
        if 'SOLD' in key['node']['edge_media_to_caption']['edges'][0]['node']['text']:
            text = 'Verkauft'
        elif 'RESERVED' in key['node']['edge_media_to_caption']['edges'][0]['node']['text']:
            text = 'Verkauft'
        else:
            textList = re.findall('dm to buy<3\\n\\n(.*)\\n',
                                  key['node']['edge_media_to_caption']['edges'][0]['node']['text'])
            text = textList[0]

        result.append([key['node']['display_url'], key['node']['edge_liked_by']['count'], text])
    return result


def saveIMG(data):
    urls = []

    for x in data:
        urlLinkImage = x[0]
        name = "image" + urlLinkImage[-22:] + ".png"
        urllib.urlretrieve(urlLinkImage, name)
        img = Image.open(name)
        img.save("images/" + name)
        urls.append("images/" + name)

    return urls


def statisticData(data):
    artikelWorstUrl = artikelWorstLike = artikelBestUrl = artikelBestLike = artikelNotSold = artikelSold = 0
    biggestLikeUrl = lowestLikeUrl = biggestLike = lowestLike = 0

    for x in data:
        url = x[0]
        like = x[1]
        mode = x[2]
        # wie viele Artikel verkauft & nicht verkauft sind
        if mode == 'Verkauft':
            artikelSold += 1
        else:
            artikelNotSold += 1

        # welcher Artikel hat die meisten Likes
        if like > biggestLike:
            biggestLike = like
            biggestLikeUrl = url
            # welches war der beste Artikel (verkauft und die meisten Likes)
            if mode == 'Verkauft':
                artikelBestLike = like
                artikelBestUrl = url

    for y in data:
        url = y[0]
        like = y[1]
        mode = y[2]
        # welcher Artikel hat die wenigsten Likes
        if like < biggestLike:
            lowestLike = like
            lowestLikeUrl = url
            # welches war der schlechteste Artikel (nicht verkauft und die wenigsten Likes)
            if mode != 'Verkauft':
                artikelWorstLike = like
                artikelWorstUrl = url

    # war es eine gute Woche? (mehr verkauft als nicht verkauft?)
    goodWeek = 1
    if artikelNotSold > artikelSold:
        goodWeek = 0

    result = {
        "abiggestLikeUrl": biggestLikeUrl,
        "abiggestLike": biggestLike,
        "alowestLike": lowestLike,
        "alowestLikeUrl": lowestLikeUrl,
        "aWorstUrl": artikelWorstUrl,
        "aWorst": artikelWorstLike,
        "aBestUrl": artikelBestUrl,
        "aBest": artikelBestLike,
        "aNotSold": artikelNotSold,
        "aSold": artikelSold,
        "goodWeek": goodWeek,
    }
    return result

def sendMail():
    message = Mail(
        from_email='sarah@treyer.one',
        to_emails='sarah_treyer@yahoo.com',
        subject='Cybernetic Vintage Report',
        html_content='<strong>Hello:) <br> Here is the new Report from Cybernetic Vintage!</strong><br>')

    with open('instagramReport.pdf', 'rb') as f:
        data = f.read()
        f.close()
    encoded_file = base64.b64encode(data).decode()

    attachedFile = Attachment(
        FileContent(encoded_file),
        FileName('cybernetic_vintage.pdf'),
        FileType('application/pdf'),
        Disposition('attachment')
    )
    message.attachment = attachedFile

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print('Success! Status:' + str(response.status_code))
    except Exception as e:
        print('Error'+ e.message)

data = getData()
pictureUrls = saveIMG(data)
statistic = statisticData(data)
addDataToPDF(data, pictureUrls, statistic)
sendMail()