from selenium import webdriver
import csv
import time
import sys


# Contains the information needed for each post, including the link to it for later navigation
class Post:

    def __init__(self, title, category, link):
        self.comments = []
        self.title = title
        self.category = category
        self.tags = []
        self.text = ""
        self.link = link

    def add_comment(self, comment):
        self.comments.append(comment)
        return self.comments

    def add_tag(self, tag):
        self.tags.append(tag)
        return self.tags


# Change to whatever browser/webdriver you're using
DRIVER_PATH = 'A:\WebScrapingSelenium\chromedriver'
driver = webdriver.Chrome(executable_path=DRIVER_PATH)

# Change for output csv location. Will open in append, so will not overwrite
CSV_PATH = 'output.csv'

# Debug flag. Set to true for print statements to the console
DEBUG = True


def start():
    # Changes for each overall category (i.e. Get Help, Community, etc.) depending on command line arguments
    # Defaults to the whole forum
    if len(sys.argv) == 2 or len(sys.argv) == 3:
        driver.get(sys.argv[1])
    else:
        driver.get('https://discuss.codecademy.com/')


def close():
    driver.close()


def scroll(pause_time):
    # Scrolls to the end of an infinitely scrolling page - taken from
    # https://stackoverflow.com/questions/20986631/how-can-i-scroll-a-web-page-using-selenium-webdriver-in-python

    if DEBUG: print('Scrolling')

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(pause_time)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    if DEBUG: print('Finished Scrolling')


# Scrapes a single subcategory
# Takes as argument the link to the subcategory and the name of the subcategory
def scrape_subcategory(subcategory_link, subcategory):
    driver.get(subcategory_link)

    if DEBUG: print('Visited subcategory', subcategory)

    # Scrolls to the end of the subcategory's page. Needs to be this long in order to deal with the increasing time
    # needed to load later pages
    scroll(5)

    # Finds the list of posts
    table = driver.find_element_by_class_name('topic-list')
    rows = table.find_elements_by_tag_name('tr')
    if DEBUG: print('Found posts')
    # Ignores the first row, which is just the names of the columns (Title, Views, Activity)
    rows = rows[1:]

    posts = []

    index = 0

    # Collects the information from each post (title, tags, and link to the post)
    # Puts it all into a Post object, which is added to the list for later output into .csv
    for row in rows:
        if DEBUG: print('Starting Row', index)
        title = row.find_element_by_class_name('main-link').find_element_by_class_name('link-top-line').\
            find_element_by_class_name('title').text
        link = row.find_element_by_class_name('main-link').find_element_by_class_name('link-top-line').\
            find_element_by_class_name('title').get_attribute('href')
        post = Post(title, subcategory, link)
        outer_tags = row.find_element_by_class_name('main-link').find_element_by_class_name('link-bottom-line').\
            find_elements_by_class_name('discourse-tags')
        if len(outer_tags) > 0:
            tags = outer_tags[0].find_elements_by_class_name('discourse-tag')
            for tag in tags:
                post.add_tag(tag.text)

        posts.append(post)

        index += 1

    if DEBUG: print('Finished Finding Posts')

    # Travels to each post using the link obtained earlier, and grabs the remaining information
    for post in posts:
        if DEBUG: print('Visiting post', post.title)
        driver.get(post.link)

        # Scrolls to the end of the comments
        # Doesn't need a long time because there aren't thousands of comments
        scroll(0.5)

        outer_posts = driver.find_element_by_tag_name('body').find_element_by_id('main').find_element_by_class_name(
            'ember-view').find_element_by_id('main-outlet').find_element_by_class_name(
            'regular').find_element_by_class_name('posts').find_element_by_class_name(
            'row').find_element_by_class_name('topic-area').find_element_by_class_name(
            'posts-wrapper').find_elements_by_tag_name('div')

        inner_posts = outer_posts[1].find_element_by_class_name('post-stream').\
            find_elements_by_class_name('topic-post')

        # The first post is the content of the original post
        content = inner_posts[0].find_element_by_class_name('onscreen-post').find_element_by_class_name('row').\
            find_element_by_class_name('topic-body').find_element_by_class_name('contents').\
            find_element_by_class_name('cooked')

        post.text = content.text

        # The remaining posts are the comments
        for i in range(1, len(inner_posts)):
            inner_rows = inner_posts[i].find_element_by_class_name('onscreen-post').\
                find_elements_by_class_name('row')
            for inner_row in inner_rows:
                topics = inner_row.find_elements_by_class_name('topic-body')
                if len(topics) > 0:
                    comment = topics[0].find_element_by_class_name('contents').find_element_by_class_name('cooked')
                    post.add_comment(comment.text)
                    break

    posts_array = [[post.title, '\n'.join(post.comments), post.category, ' '.join(post.tags), post.text]
                   for post in posts]

    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write everything to the csv
        writer.writerows(posts_array)

    if DEBUG: print('Finished Writing Posts in', category)


# Scrapes a single category
def scrape_category(category_link):
    driver.get(category_link)

    time.sleep(10)
    if DEBUG: print('Visiting category')

    subcategory_list = driver.find_element_by_tag_name('body').find_element_by_id('main'). \
        find_element_by_class_name('ember-view').find_element_by_id('main-outlet'). \
        find_element_by_class_name('list-container').find_elements_by_class_name('row')[0]. \
        find_element_by_class_name('full-width').find_element_by_id('header-list-area'). \
        find_element_by_class_name('contents').find_element_by_class_name('category-boxes'). \
        find_elements_by_class_name('category-box')

    subcategory_list_array = [[subcategory.find_element_by_class_name('category-box-inner').
                               find_element_by_class_name('category-details').
                               find_element_by_class_name('category-box-heading').find_element_by_tag_name('a').
                               get_attribute('href'),
                               subcategory.find_element_by_class_name('category-box-inner').
                               find_element_by_class_name('category-details').
                               find_element_by_class_name('category-box-heading').find_element_by_tag_name('a').
                               find_element_by_tag_name('h3').text] for subcategory in subcategory_list]

    for subcategory in subcategory_list_array:
        scrape_subcategory(subcategory[0], subcategory[1])


# Defaults to scraping the entire website
# To scrape a single category (Get Help, Community, etc.), provide the link to that category as the first argument only
# To scrape a single subcategory (Python, Java, etc.), provide the link to that subcategory as the first argument and
#   the name of the subcategory as the second argument
if __name__ == "__main__":
    start()

    if len(sys.argv) == 3:
        scrape_subcategory(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
        scrape_category(sys.argv[1])
    else:
        if DEBUG: print('Scraping all forums')
        category_list = driver.find_element_by_tag_name('body').find_element_by_id('main').\
            find_element_by_class_name('ember-view').find_element_by_id('main-outlet').\
            find_element_by_class_name('list-container').find_elements_by_class_name('row')[1].\
            find_element_by_class_name('full-width').find_element_by_id('list-area').\
            find_element_by_class_name('contents').find_element_by_class_name('ember-view').\
            find_element_by_class_name('category-list').find_element_by_tag_name('tbody').\
            find_elements_by_tag_name('tr')
        category_list_array = [category.find_element_by_class_name('category').find_element_by_tag_name('h3').
                               find_element_by_tag_name('a').get_attribute('href') for category in category_list]

        for category in category_list_array:
            scrape_category(category)

    close()
