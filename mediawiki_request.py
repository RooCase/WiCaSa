import requests
from ipaddress import ip_address, ip_network
from threading import Thread
from queue import Queue, Empty
import json
import IP_Data

def CIDRIP(ip):
    """
    This function takes in the CIDR notation of an IP address and returns a list of all
    possible IP addresses in that range.
    """
    # Split the CIDR notation into IP address and prefix length
    ip, prefix = ip.split('/')

    # Create an IP network object using the given CIDR notation
    network = ip_network(f"{ip}/{prefix}", strict=False)

    # Generate a list of all possible IP addresses in the network
    return [str(ip) for ip in network.hosts()]

def get_articles_in_category(category):
    """
    This function takes in a category name and returns a list of all articles in that category.
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmlimit": "max",
        "format": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Extract the titles of the articles from the response
    articles = [member['title'] for member in data.get('query', {}).get('categorymembers', [])]
    return articles
    
def get_all_all_articles(category, max_depth=1, file_path="articles.txt"):
    """
    This function takes in a category name and returns a list of all articles in that category,
    including articles in subcategories.
    """
    output = []
    queue = Queue()

    for article in get_articles_in_category(category):
        queue.put((article, 1))

    def worker():
        with open(file_path, "a") as f:
            while True:
                try:
                    article, depth = queue.get(timeout=2)
                except Empty:
                    # print("Queue is empty, exiting worker thread.")
                    break

                try:
                    if depth > max_depth:
                        continue

                    if article.startswith("Category:"):
                        print(f"Working on: {article}")
                        subcategory = article[len("Category:"):]
                        subcats = get_articles_in_category(subcategory)
                        for sub_article in subcats:
                            queue.put((sub_article, depth + 1))
                    else:
                        f.write(article + "\n")


                except requests.exceptions.RequestException as e:
                    print(f"Request failed for {article}: {e}")
                except Exception as e:
                    print(f"Error processing {article}: {e}")
                finally:
                    queue.task_done()

    threads = []
    num_threads = 10

    for _ in range(num_threads):
        t = Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)

    queue.join()

    for t in threads:
        t.join(timeout=1)

    return output

def remove_duplicates(lst):
    """
    This function takes in a list and removes duplicates while preserving the order.
    """
    seen = set()
    return [x for x in lst if not (x in seen or seen.add(x))]

def get_revision_history(articles, start_time, end_time, ip_only=False):
    """
    Returns the list of revisions for a list of articles within a specific time range.
    If ip_only is True, only includes revisions where the user is an IP address.
    Each thread processes one article at a time.
    """
    print(f"Getting revision history for articles")
    url = "https://en.wikipedia.org/w/api.php"
    all_revisions = []
    queue = Queue()
    num_threads = 5  # Adjust the number of threads as needed

    def worker():
        while not queue.empty():
            with open("IPaddresses.txt", "a") as f:
                try:
                    article_title = queue.get()
                    print(f"Processing article: {article_title}")
                    article_revisions = []
                    params = {
                        "action": "query",
                        "prop": "revisions",
                        "titles": article_title,
                        "rvstart": start_time,  # must be newer time
                        "rvend": end_time,      # must be older time
                        "rvlimit": "max",
                        "rvprop": "ids|timestamp|user|comment|flags",
                        "format": "json"
                    }

                    while params:
                        response = requests.get(url, params=params)
                        data = response.json()

                        pages = data.get("query", {}).get("pages", {})
                        for page_id, page_data in pages.items():
                            revisions = page_data.get("revisions", [])
                            if ip_only:
                                filtered = []
                                for rev in revisions:
                                    try:
                                        ip_address(rev.get('user', ''))
                                        filtered.append(rev)
                                        f.writelines((str(rev.get('user', '')) + "\n"))
                                    except ValueError:
                                        continue
                                revisions = filtered
                            article_revisions.extend(revisions)

                        params = {**params, **data.get('continue', {})} if 'continue' in data else None

                    all_revisions.append({"title": article_title, "revisions": article_revisions})
                except Exception as e:
                    print(f"Error fetching revisions for {article_title}: {e}")
                finally:
                    queue.task_done()

    # Add articles to the queue
    for article in articles:
        queue.put(article)

    # Create and start threads
    threads = []
    for _ in range(num_threads):
        thread = Thread(target=worker)
        thread.start()
        threads.append(thread)

    queue.join()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    return all_revisions

def read_existing_articles(file_path):
    """
    This function reads a file and returns a list of articles.
    """
    with open(file_path, "r") as f:
        articles = f.read().splitlines()
    return articles
