# Retailer-Specific Checkout Patterns

This reference documents known checkout patterns for major retailers to speed up coupon testing.

## Major Retailers

### Amazon
- **Checkout URL**: `amazon.com/gp/buy/spc/handlers/display.html`
- **Coupon Expand**: "Enter a gift card, share card, or promotional code"
- **Coupon Field**: `gc-redemption-input`
- **Apply Button**: `gc-redemption-apply-button`
- **Success**: "Promotional code applied"
- **Error**: "code is invalid"
- **Notes**: Distinguish gift cards vs promo codes. Some codes are Subscribe & Save only.

### Target
- **Checkout URL**: `target.com/co-cart`
- **Coupon Expand**: "Enter a promo code"
- **Coupon Field**: `promoCodeInput`
- **Apply Button**: "Apply"
- **Success**: "Promo code applied"
- **Error**: "not valid"
- **Notes**: Some codes require Target Circle. RedCard gives automatic 5% off.

### Walmart
- **Checkout URL**: `walmart.com/cart`
- **Coupon Expand**: "Apply promo code"
- **Coupon Field**: `promoCode`
- **Apply Button**: "Apply"
- **Success**: "Promo applied"
- **Error**: "not recognized"
- **Notes**: Some codes are Walmart+ exclusive. Many codes are store-only.

### Best Buy
- **Checkout URL**: `bestbuy.com/cart`
- **Coupon Expand**: "Enter promo code"
- **Coupon Field**: `promoCode`
- **Apply Button**: "Apply"
- **Success**: "discount applied"
- **Error**: "invalid"
- **Notes**: Most codes are product-specific. Student/military codes available.

### Costco
- **Checkout URL**: `costco.com/CheckoutCartView`
- **Coupon Field**: `promoCode`
- **Apply Button**: "Apply"
- **Notes**: Requires membership login. Limited online promo codes.

### Home Depot
- **Checkout URL**: `homedepot.com/mycart`
- **Coupon Expand**: "Apply Promo Code"
- **Coupon Field**: `promoCode`
- **Notes**: Pro Xtra members have exclusive codes.

### Kohl's
- **Checkout URL**: `kohls.com/checkout/shopping_bag.jsp`
- **Coupon Field**: `promoCode`
- **Notes**: Complex stacking rules. Kohl's Cash + promo codes often combinable.

### Macy's
- **Checkout URL**: `macys.com/bag`
- **Coupon Field**: `promoCode`
- **Notes**: Star Rewards members have exclusive codes. Beauty often excluded.

### Nike
- **Checkout URL**: `nike.com/cart`
- **Coupon Field**: `promoCode`
- **Notes**: Member-only codes common. Sale items usually excluded.

### Sephora
- **Checkout URL**: `sephora.com/basket`
- **Coupon Expand**: "Add Promo Code"
- **Notes**: Often free sample codes, not discounts. Rouge/VIB exclusive codes.

---

## Coupon Aggregator URLs

| Aggregator | URL Pattern |
|------------|-------------|
| RetailMeNot | `retailmenot.com/{retailer}` |
| CouponFollow | `couponfollow.com/{retailer}` |
| Slickdeals | `slickdeals.net/coupons/{retailer}/` |
| DontPayFull | `dontpayfull.com/at/{retailer}` |
| Groupon | `groupon.com/coupons/{retailer}` |

---

## Common Code Patterns

| Type | Pattern | Example |
|------|---------|---------|
| Percentage | `SAVE\d+`, `\d+OFF` | SAVE20, 15OFF |
| Fixed Amount | `\d+DOLLARS`, `GET\d+` | 10DOLLARS |
| Free Shipping | `FREESHIP`, `SHIPFREE` | FREESHIPPING |
| First Order | `WELCOME`, `NEW`, `FIRST` | WELCOME10 |
| Seasonal | `BF{year}`, `CYBER`, `HOLIDAY` | BF2025 |

---

## Testing Priority

1. Percentage codes (highest potential)
2. Fixed amount codes (guaranteed savings)
3. Free shipping (if not already free)
4. Category-specific codes
5. New customer codes

---

## Known Quirks

- **Amazon**: Promo vs gift card fields differ
- **Target**: RedCard stacks with promo codes
- **Kohl's**: Most complex stacking rules
- **Nordstrom**: Rarely offers promo codes
- **Nike**: Sale items usually excluded
