# Hebrew and RTL reference

Everything here was found by rendering a page and looking at the screenshot.
None of it is visible when reading HTML source, which is why it survives review.

## Why bidirectional text reorders

Unicode assigns every character a direction: strong (Hebrew is RTL, Latin
letters are LTR), weak (digits), or neutral (space, comma, hyphen, bullet,
period, slash). Neutrals have no direction of their own, so the bidi algorithm
attaches each one to its surroundings. When a neutral sits between two runs of
*different* direction, it resolves to the paragraph direction — and can end up
rendered on the opposite side from where you typed it.

The practical consequence: a string that is pure Hebrew is always safe, and a
string mixing Hebrew with Latin words or numbers is only safe if you isolate
the foreign runs.

## The failure catalogue

### Two numbers around a separator — reverses

```html
<!-- renders "24:00 — 18:00" -->
<td>18:00 — 24:00</td>

<!-- correct -->
<td><bdi dir="ltr">18:00 – 24:00</bdi></td>
```

The em-dash is neutral and sits between two weak digit runs, so the whole
expression takes the paragraph's RTL order and the two times swap. This hits
opening hours, price ranges, date ranges, and score lines.

### A Latin word inside a Hebrew sentence — drags neighbours

```html
<!-- scrambles: the "· 52" migrates next to "Google" -->
<strong>4.9</strong> ב-Google · 52 ביקורות

<!-- correct -->
<strong>4.9</strong> ב־<bdi>Google</bdi> · 52 ביקורות
```

`<bdi>` (bidi isolate) tells the algorithm to resolve the element's contents
independently and treat the whole thing as a single neutral-free unit from the
outside. It is the right tool almost every time — it needs no `dir` guess and
it cannot leak.

### A digit before a comma — comma jumps

```html
<!-- renders "קרל פופר ,7 נתניה" -->
<p>קרל פופר 7, נתניה</p>

<!-- correct -->
<p>קרל פופר 7&rlm;, נתניה</p>
```

`&rlm;` (U+200F RIGHT-TO-LEFT MARK) is an invisible strong-RTL character. Placed
after the digit it gives the following comma an RTL neighbour to attach to.

Use `&rlm;` for a single stray neutral after digits; use `<bdi>` when wrapping a
whole foreign token. Both are fine — `<bdi>` is more readable in markup.

### Phone numbers

`052-399-1601` renders correctly unassisted: it is one continuous weak run with
internal neutrals, so it stays together. No fix needed. Don't add one — an
unnecessary `dir="ltr"` on a phone number can push it away from its label.

## Layout

Use logical properties so the layout follows `dir` rather than hardcoding sides:

| Physical | Logical |
|---|---|
| `margin-left` | `margin-inline-start` |
| `padding-right` | `padding-inline-end` |
| `left: 0; right: 0` | `inset-inline: 0` |
| `border-left` | `border-inline-start` |
| `text-align: left` | `text-align: start` |

Two that are **not** logical and will mislead you:

- `transform-origin` takes physical keywords only. `inline-start` is invalid and
  is silently dropped, leaving the default. Use percentages (`0%` / `100%`).
- `direction` on a flex container flips visual order of items, so in RTL the
  first DOM child renders rightmost. That is usually what you want; just be
  aware when a screenshot looks "backwards" that it may be correct.

Keyboard navigation in a tablist should follow visual order: in RTL,
`ArrowLeft` moves to the *next* tab and `ArrowRight` to the previous.

## Fonts

Google Fonts is often unreachable from sandboxes, so a page can look wrong in
your screenshots and correct in production. Check before concluding the CSS is
broken:

```js
await page.evaluate(() => Array.from(document.fonts).map(f => f.family + ':' + f.status))
// [] means nothing loaded — network, not CSS
```

Reasonable Hebrew stacks:

```css
--sans:  'Heebo', system-ui, -apple-system, 'Segoe UI', 'Noto Sans Hebrew', Arial, sans-serif;
--serif: 'Frank Ruhl Libre', 'Narkisim', 'Times New Roman', Georgia, serif;
```

`text-transform: uppercase` does nothing to Hebrew, which has no case — it is
harmless on mixed labels but will not give you the small-caps look you may be
reaching for. Generous `letter-spacing` on Hebrew reads as deliberate at small
sizes (eyebrows, labels) and hurts legibility in running text.

## Verifying

```js
// after loading the page
await page.evaluate(() => ({
  dir: getComputedStyle(document.documentElement).direction,   // expect "rtl"
  overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth, // expect 0
}))
```

Then screenshot and read the image. Specifically check: opening hours, any
price or score line, the address, and anything containing a Latin brand name.
