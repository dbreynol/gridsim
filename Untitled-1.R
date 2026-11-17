

set.seed(0815)

N <- 500

ab_test_data <- data.frame( order_id = 1:N,

revenue = rlnorm(N, meanlog = 3.8, sdlog = 0.3),

processing_days = rnorm(N, mean = 4.3, sd = 1.2),

client_is_enterprise = rbinom(N, size = 1, prob = 0.18) )

hist_mu_rev <- 45
hist_sd_rev <- 15
hist_mu_del <- 4.5
hist_sd_del <- 1.2
hist_p_ent <- 0.15
n <- 500

# Extract our sample statistics
sample_mean_del <- mean(ab_test_data$processing_days) # ~4.311867
sample_mean_rev <- mean(ab_test_data$revenue)         # ~47.75818
sample_p_ent <- mean(ab_test_data$client_is_enterprise)      # ~0.196

# Q1 Solution
se_del <- hist_sd_del / sqrt(n)
q1_prob <- pnorm(sample_mean_del, mean = hist_mu_del, sd = se_del)
q1_prob

# Q2 solution
se_rev <- hist_sd_rev / sqrt(n)

(sample_mean_rev - hist_mu_rev)/se_rev
#q2_prob <- pnorm(sample_mean_rev, mean = hist_mu_rev, sd = se_rev, lower.tail = FALSE)
#q2_prob

se_prop <- sqrt((hist_p_ent * (1 - hist_p_ent)) / n)
q3_prob <- pnorm(sample_p_ent, mean = hist_p_ent, sd = se_prop, lower.tail = FALSE)
q3_prob
