/*
 * Menu / price list. This is the one file a non-developer edits.
 *
 * Shape: category -> groups -> items. `note` is the second, grey line under a
 * name (description, region, variant) and may be ''.
 *
 * A category whose groups are all empty renders nothing at all, which is what
 * makes it safe to commit a stub for a section whose photos have not arrived
 * yet — it simply appears once it has items.
 *
 * Order categories the way a visitor browses, not the way the owner's booking
 * platform happens to file them.
 */

const MENU = [
  {
    id: 'food',
    title: 'אוכל',
    groups: [
      {
        title: 'ראשונות',
        items: [
          { name: 'שם המנה', note: 'תיאור קצר, רכיבים עיקריים', price: 48 },
        ],
      },
    ],
  },

  {
    id: 'drinks',
    title: 'שתייה',
    groups: [
      {
        title: 'קוקטיילים',
        items: [
          { name: 'שם הקוקטייל', note: 'רכיבים', price: 58 },
        ],
      },
    ],
  },

  {
    id: 'pending',
    title: 'קטגוריה שטרם התקבלה',
    groups: [
      // Empty on purpose: hidden until it has items.
    ],
  },
];
