Investigating Media Quarterback Coverage
========================================

This code gets word counts for media coverage of NFL quarterbacks.  It downloads 
sentences from [MediaCloud](https://mediacloud.org) and does simple stopwording and 
word counting.  The resulting data is stored in the `data` folder so you can do analysis 
on it.


Installing
----------

 * This code uses Python 2.7.
 * Register to get a [MediaCloud API Key]( https://core.mediacloud.org/login/register ). You will be able to see the key on [your profile page]( https://core.mediacloud.org/admin/profile ) once you are registered.
 * Copy the `config.txt.template` to `config.txt` and then paste in your API key where indicated. 
 * Install the dependencies via pip: `pip install -r requirements.pip`

Fetching Media Coverage Data
----------------------------

Once you have set it all up, just run `sentencedownload.py` to get all the sentences and build wordcounts.  This doesn't use the MediaCloud word counting because we do not want to sample the data; we want the true full word counts to support this analysis.

Analyzing Data
--------------

We're using [Jupyter Notebooks](http://jupyter.org) for analysis. Open up the `qb-analysis.ipynb` to start exploring.

Methodology
-----------

### Determining Race

We [scraped Wikipedia and nfl.com](https://github.com/c4fcm/nfl-quarterback-scraper) to generate a list of regular season starting quarterbacks.  Then we added a column for "race" (see `qb-table.csv`).  Race determination is a thorny and difficult task. Ideally, we would categorize using each player's self-identified race. However, we were unable to find evidence of self-identification for any of the players.  For this project, we elected to use the categorizations found in [Best Ticket's unofficial 2014 NFL Player Census]( http://www.besttickets.com/blog/nfl-player-census-2014/ ).  To support testing our hypotheses we group players as either "white" or "other" (ie. non-white).

### Sources

We created a list of sources including [US Mainstream Media](https://sources.mediameter.org/#media-tag/8875027/details), [US Regional Media](https://sources.mediameter.org/#media-tag/2453107/details), and the top US sports websites (as identified by Alexa rankings).  These are listed with their MediaCloud ids in `sources.csv`.

### English Stopwords

Our initial list of english stopwords is listed in `stop-words-english4.txt`.  This list combines various other stopword lists into one larger one to remove more words we don't want for our analysis.

### Domain-Specific Stop-Words

We took the top 200 words for both "white" and "other" and coded them to identify domain-specific stopwords (ie. "pass", "twitter", etc.).  We coded into the following categories:
 * health (injury, knee)
 * football stop word (quarterback)
 * name (Newton)
 * descriptors (smart, fast) 
 * action (passed, caught, run)
 * personal (career, top, performance, other)

The results are saved in `manual-word-tags.csv`.

Contributors
------------
 * [Allan Ko](https://github.com/allanko)
 * [Rahul Bhargava](https://github.com/rahulbot)
 * [Val Healy](https://github.com/val1ant)
 
