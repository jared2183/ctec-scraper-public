from bs4 import BeautifulSoup
# import codecs
# import json

def scrape_ctec(page_source): 

    # Create the payload
    soup = BeautifulSoup(page_source, 'html.parser')

    instr_mean = soup.find_all('td', class_='TabularBody_RightColumn_NoWrap')[1].text.strip()
    instr_count = soup.find_all('td', class_='TabularBody_RightColumn_NoWrap')[0].text.strip()

    course_mean = soup.find_all('td', class_='TabularBody_RightColumn_NoWrap')[3].text.strip()
    course_count = soup.find_all('td', class_='TabularBody_RightColumn_NoWrap')[2].text.strip()

    comments = soup.find('div', class_='CommentBlockRow TableContainer').find_all('td', class_='TabularBody_LeftColumn')

    ctec_content = {
        'instr_rating': {'mean': instr_mean, 'count': instr_count},
        'course_rating': {'mean': course_mean, 'count': course_count},
        'comments': [comment.text.strip() for comment in comments]
    }

    return ctec_content

# f = codecs.open("scraper/example_ctec.html",'r')
# data = scrape_ctec(f.read())
# print(data)

# with open('result.json', 'w') as out:
#     json.dump(data, out, indent=4)
# print('Wrote to file.')
