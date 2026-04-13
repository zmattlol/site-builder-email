const test = require("node:test");
const assert = require("node:assert/strict");

const { buildEmail } = require("../src/emailTemplate");

test("buildEmail creates a soft outreach message with personalized details", () => {
  const result = buildEmail({
    recipientName: "Jamie",
    businessName: "Riverstone Plumbing",
    businessType: "plumbing",
    city: "Denver",
    offerSummary: "building and setting up a personalized website for your business",
    benefit1: "understand your services quickly",
    benefit2: "request a quote online",
    benefit3: "call you from any device",
    callToAction:
      "If that sounds useful, I would be happy to share a couple of ideas for your business.",
    senderName: "Alex",
    senderEmail: "alex@example.com",
  });

  assert.equal(result.subject, "Riverstone Plumbing website idea for Denver");
  assert.match(result.text, /Hi Jamie,/);
  assert.match(result.text, /Riverstone Plumbing/);
  assert.match(result.text, /understand your services quickly, request a quote online, and call you from any device/);
  assert.match(result.text, /If that sounds useful/);
  assert.match(result.text, /Alex/);
  assert.match(result.text, /alex@example.com/);
});

test("buildEmail falls back to generic defaults when optional fields are blank", () => {
  const result = buildEmail({
    businessName: "Oak & Pine Studio",
    senderName: "Taylor",
    senderEmail: "taylor@example.com",
  });

  assert.equal(result.subject, "Oak & Pine Studio: a personalized website");
  assert.match(result.text, /Hi there,/);
  assert.match(result.text, /I noticed you may not have a dedicated website yet/);
  assert.match(result.html, /<p>/);
});
