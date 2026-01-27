# library(tidyr)
library(rvest)
library(dplyr)
library(purrr)
library(stringr)
library(readr)

base_url <- "https://statistiky.debatovani.cz/"
list_url <- paste0(base_url, "?page=lide")

# Get list of people
people_page <- read_html(list_url)

people_nodes <- html_elements(people_page, "td:nth-child(1) a")

people_df <- tibble(
    name = html_text(people_nodes, trim = TRUE),
    href = html_attr(people_nodes, "href")
) %>%
    mutate(
        id = str_extract(href, "(?<=clovek_id=)\\d+")
    ) %>%
    filter(!is.na(id))



# Filter to names in debater_names.txt
debater_names <- read_lines("debater_names.txt") %>%
    str_trim() %>%
    discard(~ .x == "") %>%
    unique()

people_df <- people_df %>%
    filter(name %in% debater_names)

# Function to scrape debates for a person
scrape_person_debates <- function(id, name) {
    debates_url <- paste0(base_url, "?page=clovek.debaty&clovek_id=", id)
    debates_page <- read_html(debates_url)
    
    dates <- html_elements(debates_page, "td:nth-child(1)") %>%
        html_text(trim = TRUE)
    
    scores <- html_elements(debates_page, "td:nth-child(8)") %>%
        html_text(trim = TRUE)
    
    # Align lengths (keep only complete rows)
    n <- min(length(dates), length(scores))
    if (n == 0) {
        return(tibble(id = character(), name = character(), debate_date = character(), speaker_score = character()))
    }
    
    tibble(
        id = id,
        name = name,
        debate_date = dates[seq_len(n)],
        speaker_score = scores[seq_len(n)]
    ) %>%
        mutate(debate_date = as.Date(debate_date)) %>%
        filter(!is.na(debate_date)) %>%
        arrange(debate_date) %>%
        slice_head(n = 10) %>%
        mutate(debate_date = format(debate_date, "%Y-%m-%d"))
}

# Scrape all filtered people with progress every 10%
total <- nrow(people_df)
last_pct <- -10

results <- pmap_dfr(
    list(
        id = people_df$id,
        name = people_df$name,
        idx = seq_len(total)
    ),
    function(id, name, idx) {
        if (total > 0) {
            pct <- floor((idx / total) * 100)
            if (pct %% 10 == 0 && pct != last_pct) {
                message(sprintf("Progress: %d%%", pct))
                last_pct <<- pct
            }
        }
        scrape_person_debates(id, name)
    }
)


# Save CSV
write_csv(results, "speaker_scores.csv")