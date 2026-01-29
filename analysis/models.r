library(dplyr)
library(readr)
library(lubridate)
library(plm)
library(stringr)

base_dir <- "c:/Users/QX163MQ/Downloads/non-work/school/data processing in python/project/speaker_stats"
scores_path <- file.path(base_dir, "scraping/debate_natural_ability_scraping/speaker_scores.csv")
final_path  <- file.path(base_dir, "data/processed/final_joined_data.csv")

clean_name <- function(x) {
    x %>%
        str_replace_all('"[^"]*"', "") %>%  # remove nicknames in quotes
        str_squish()
}

# Load and prep speaker_scores
scores <- read_csv(scores_path, show_col_types = FALSE) %>%
    mutate(
        debate_date = ymd(debate_date),
        speaker_score_num = suppressWarnings(as.numeric(speaker_score)),
        name_clean = clean_name(name)
    ) %>%
    filter(!is.na(debate_date), !is.na(speaker_score_num), !is.na(name_clean)) %>%
    arrange(name_clean, debate_date)

avg_first10 <- scores %>%
    group_by(name_clean) %>%
    slice_head(n = 10) %>%
    summarise(avg_first10_score = mean(speaker_score_num), .groups = "drop")

avg_first10_strict <- scores %>%
    group_by(name_clean) %>%
    filter(n() >= 10) %>%
    slice_head(n = 10) %>%
    summarise(avg_first10_score = mean(speaker_score_num), .groups = "drop")

# Load final data
df <- read_csv(final_path, show_col_types = FALSE) %>%
    mutate(
        speaker_name_clean = str_squish(speaker_name),
        debate_date = ymd_hms(debate_date),
        speaker_first_debate_date = ymd(speaker_first_debate_date)
    ) %>%
    inner_join(avg_first10, by = c("speaker_name_clean" = "name_clean"))

# Feature engineering (same as notebook)
motion_balance <- df %>%
    filter(side == "aff") %>%
    group_by(debate_id, motion) %>%
    summarise(ballots_gained = mean(ballots_gained, na.rm = TRUE), .groups = "drop") %>%
    group_by(motion) %>%
    summarise(motion_balance = mean(ballots_gained, na.rm = TRUE), .groups = "drop")

df <- df %>%
    left_join(motion_balance, by = "motion") %>%
    mutate(
        years_since_first_debate = year(debate_date) - year(speaker_first_debate_date),
        tournament_round = ave(debate_date, tournament_id, FUN = function(x) rank(x, ties.method = "first")),
        is_aff = if_else(side == "aff", 1, 0),
        motion_balance_x_aff = motion_balance * is_aff
    )

get_teammate_avg <- function(x) {
    sapply(seq_along(x), function(i) mean(x[-i], na.rm = TRUE))
}

df <- df %>%
    group_by(debate_id, side) %>%
    mutate(avg_teammate_score = get_teammate_avg(speaker_points)) %>%
    ungroup() %>%
    arrange(speaker_name_clean, debate_date, debate_id) %>%
    group_by(speaker_name_clean) %>%
    mutate(lag_avg_teammate_score = lag(cummean(avg_teammate_score))) %>%
    ungroup()

# Model data
df_model <- df %>%
    filter(
        !is.na(speaker_points),
        !is.na(avg_first10_score),
        !is.na(lag_avg_teammate_score),
        !is.na(tournament_round),
        !is.na(motion_balance),
        !is.na(motion_balance_x_aff)
    ) %>%
    mutate(speaker_id = as.integer(as.factor(speaker_name_clean))) %>%
    arrange(speaker_id, debate_date)

df_model_strict <- df %>%
    select(-avg_first10_score) %>%
    inner_join(avg_first10_strict, by = c("speaker_name_clean" = "name_clean")) %>%
    filter(
        !is.na(speaker_points),
        !is.na(avg_first10_score),
        !is.na(lag_avg_teammate_score),
        !is.na(tournament_round),
        !is.na(motion_balance),
        !is.na(motion_balance_x_aff)
    ) %>%
    mutate(speaker_id = as.integer(as.factor(speaker_name_clean))) %>%
    arrange(speaker_id, debate_date)

# Pooled OLS
pool_formula <- speaker_points ~ avg_first10_score + is_male + lag_avg_teammate_score +
    tournament_round

pool_mod <- plm(pool_formula, data = df_model, model = "pooling", index = c("speaker_id", "debate_date"))

# Random Effects
re_mod <- plm(pool_formula, data = df_model, model = "random", index = c("speaker_id", "debate_date"))

# Fixed Effects (proxy will be dropped if time-invariant)
fe_mod <- plm(pool_formula, data = df_model, model = "within", index = c("speaker_id", "debate_date"))

# LM test: pooled vs RE
lm_test <- plmtest(pool_mod, type = "bp")

# Hausman test: RE vs FE
hausman_test <- phtest(fe_mod, re_mod)

pool_mod_strict <- plm(pool_formula, data = df_model_strict, model = "pooling", index = c("speaker_id", "debate_date"))

re_mod_strict <- plm(pool_formula, data = df_model_strict, model = "random", index = c("speaker_id", "debate_date"))

fe_mod_strict <- plm(pool_formula, data = df_model_strict, model = "within", index = c("speaker_id", "debate_date"))

lm_test_strict <- plmtest(pool_mod_strict, type = "bp")

hausman_test_strict <- phtest(fe_mod_strict, re_mod_strict)

print(summary(pool_mod))
print(summary(re_mod))
print(summary(fe_mod))
print(lm_test)
print(hausman_test)

print(summary(pool_mod_strict))
print(summary(re_mod_strict))
print(summary(fe_mod_strict))
print(lm_test_strict)
print(hausman_test_strict)


df_model_proper_time <- df_model %>%
    arrange(speaker_id, debate_date, debate_id) %>%
    group_by(speaker_id) %>%
    mutate(time_index = row_number()) %>%
    ungroup()

df_model_proper_time_strict <- df_model_strict %>%
    arrange(speaker_id, debate_date, debate_id) %>%
    group_by(speaker_id) %>%
    mutate(time_index = row_number()) %>%
    ungroup()

df_mundlak <- df_model_proper_time %>%
    group_by(speaker_id) %>%
    filter(n() >= 10) %>%
    mutate(
        mean_lag_avg_teammate_score = mean(lag_avg_teammate_score, na.rm = TRUE),
        mean_tournament_round = mean(tournament_round, na.rm = TRUE),
        lag_avg_teammate_score_c = lag_avg_teammate_score - mean_lag_avg_teammate_score,
        tournament_round_c = tournament_round - mean_tournament_round
    ) %>%
    ungroup() %>%
    mutate(
        avg_first10_score_z = as.numeric(scale(avg_first10_score)),
        lag_avg_teammate_score_c_z = as.numeric(scale(lag_avg_teammate_score_c)),
        tournament_round_c_z = as.numeric(scale(tournament_round_c)),
        mean_lag_avg_teammate_score_z = as.numeric(scale(mean_lag_avg_teammate_score)),
        mean_tournament_round_z = as.numeric(scale(mean_tournament_round))
    )

df_mundlak_strict <- df_model_proper_time_strict %>%
    group_by(speaker_id) %>%
    filter(n() >= 10) %>%
    mutate(
        mean_lag_avg_teammate_score = mean(lag_avg_teammate_score, na.rm = TRUE),
        mean_tournament_round = mean(tournament_round, na.rm = TRUE),
        lag_avg_teammate_score_c = lag_avg_teammate_score - mean_lag_avg_teammate_score,
        tournament_round_c = tournament_round - mean_tournament_round
    ) %>%
    ungroup() %>%
    mutate(
        avg_first10_score_z = as.numeric(scale(avg_first10_score)),
        lag_avg_teammate_score_c_z = as.numeric(scale(lag_avg_teammate_score_c)),
        tournament_round_c_z = as.numeric(scale(tournament_round_c)),
        mean_lag_avg_teammate_score_z = as.numeric(scale(mean_lag_avg_teammate_score)),
        mean_tournament_round_z = as.numeric(scale(mean_tournament_round))
    )

colinearity_test <- lm(speaker_points ~ lag_avg_teammate_score_c + mean_lag_avg_teammate_score + tournament_round_c + mean_tournament_round, data = df_mundlak)
summary(colinearity_test)

mundlak_formula <- speaker_points ~ avg_first10_score_z + is_male +
    lag_avg_teammate_score_c_z + tournament_round_c_z +
    mean_lag_avg_teammate_score_z + mean_tournament_round_z

mundlak_mod <- plm(
    mundlak_formula,
    data = df_mundlak,
    model = "random",
    index = c("speaker_id", "time_index")
)

mundlak_mod_strict <- plm(
    mundlak_formula,
    data = df_mundlak_strict,
    model = "random",
    index = c("speaker_id", "time_index")
)

print(summary(mundlak_mod))
print(summary(mundlak_mod_strict))

# DEBUG
df_mundlak %>%
    count(speaker_id, name = "n_obs") %>%
    arrange(n_obs)

df_mundlak %>%
    group_by(speaker_id) %>%
    summarise(
        n_obs = n(),
        var_lag = var(lag_avg_teammate_score, na.rm = TRUE),
        var_round = var(tournament_round, na.rm = TRUE)
    ) %>%
    filter(n_obs < 3 | is.na(var_lag) | var_lag == 0 | is.na(var_round) | var_round == 0)

df_mundlak %>%
    group_by(speaker_id) %>%
    summarise(
        const_lag = n_distinct(lag_avg_teammate_score) == 1,
        const_round = n_distinct(tournament_round) == 1
    ) %>%
    filter(const_lag | const_round)


# mundlak with dropped mean terms

## mundlak with dropped mean tourney round
mundlak_formula_no_mean_round <- speaker_points ~ avg_first10_score_z + is_male +
    lag_avg_teammate_score_c_z + tournament_round_c_z +
    mean_lag_avg_teammate_score_z

mundlak_no_mean_round <- plm(
    mundlak_formula_no_mean_round,
    data = df_mundlak,
    model = "random",
    index = c("speaker_id", "time_index")
)

mundlak_no_mean_round_strict <- plm(
    mundlak_formula_no_mean_round,
    data = df_mundlak_strict,
    model = "random",
    index = c("speaker_id", "time_index")
)

print(summary(mundlak_no_mean_round))
print(summary(mundlak_no_mean_round_strict))

## mundlak with dropped mean lag avg score 
mundlak_formula_no_mean_lag <- speaker_points ~ avg_first10_score_z + is_male +
    lag_avg_teammate_score_c_z + tournament_round_c_z +
    mean_tournament_round_z

mundlak_no_mean_lag <- plm(
    mundlak_formula_no_mean_lag,
    data = df_mundlak,
    model = "random",
    index = c("speaker_id", "time_index")
)

mundlak_no_mean_lag_strict <- plm(
    mundlak_formula_no_mean_lag,
    data = df_mundlak_strict,
    model = "random",
    index = c("speaker_id", "time_index")
)

print(summary(mundlak_no_mean_lag))
print(summary(mundlak_no_mean_lag_strict))



#Check rank deficiency:
m <- model.matrix(mundlak_formula, df_mundlak)
qr(m)$rank; ncol(m)

kappa(model.matrix(mundlak_formula, df_mundlak))

#Find exact linear dependencies:
alias(lm(mundlak_formula, data = df_mundlak))

#Check duplicate (speaker_id, time_index) rows:
df_mundlak %>% count(speaker_id, time_index) %>% filter(n > 1)

# duplicate rows?s

ercomp(mundlak_formula, data = df_mundlak, model = "random", effect = "individual", random.method = "swar", index = c("speaker_id", "time_index"))

pdata.frame(df_mundlak, index = c("speaker_id", "time_index")) %>%
index() %>%
table() %>%
{ .[. > 1] }