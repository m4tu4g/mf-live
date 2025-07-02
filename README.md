[temp readme]

Calculates the weighted percentage change based on live stock value change and it's percentage in a fund

# How to use

1. Visit any fund at Groww, say https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth

2. Change domain to `mf-live.gowthamkalla.com` i.e., https://mf-live.gowthamkalla.com/mutual-funds/hdfc-mid-cap-fund-direct-growth

it'll respond with JSON as below example

```json
{
    "fund": "hdfc-mid-cap-fund-direct-growth",
    "day_change_percentage": 0.13609781752561478,
    "not_found": {
        "Nesco Ltd.": 0.00797628
    },
    "not_matched": {
        "Eternal Ltd.": ["Eternal (Zomato) Ltd.", 1.07],
        "Mahindra & Mahindra Financial Services Ltd.": ["Mahindra & Mahindra Ltd.", 1.8],
        "Mahindra & Mahindra Financial Services Ltd. - Right Entitlement": ["Mahindra & Mahindra Ltd.", 0.06]
    }
}
```

`not_found` - stocks that are not found when searched, keys are stocks and values are percentages of particular stock in fund

`not_matched` - stocks that are **nearest matched by name** but not full-text when searched, keys are stocks and values are [nearest stock that is matched, percentage of particular stock in fund]

consider `day_change_percentage`'s error based on `not_found` and `not_matched`

