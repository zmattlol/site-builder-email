function normalize(value, fallback = "") {
  return String(value ?? "")
    .trim()
    .replace(/\s+/g, " ") || fallback;
}

function toSentenceCase(value) {
  if (!value) {
    return "";
  }

  return value.charAt(0).toUpperCase() + value.slice(1);
}

function buildSubject({
  businessName,
  city,
  offerSummary,
}) {
  const cleanBusinessName = normalize(businessName, "your business");
  const cleanCity = normalize(city);
  const cleanOffer = normalize(offerSummary, "a personalized website");

  if (cleanCity) {
    return `${cleanBusinessName} website idea for ${cleanCity}`;
  }

  return `${cleanBusinessName}: ${cleanOffer}`;
}

function buildBenefitsParagraph({ benefit1, benefit2, benefit3 }) {
  const benefits = [benefit1, benefit2, benefit3]
    .map((benefit) => normalize(benefit))
    .filter(Boolean);

  if (benefits.length === 0) {
    return "A simple website can help people find your services, trust your business faster, and contact you without relying only on third-party platforms.";
  }

  if (benefits.length === 1) {
    return `A simple website can make it easier for customers to ${benefits[0]}.`;
  }

  if (benefits.length === 2) {
    return `A simple website can make it easier for customers to ${benefits[0]} and ${benefits[1]}.`;
  }

  return `A simple website can make it easier for customers to ${benefits[0]}, ${benefits[1]}, and ${benefits[2]}.`;
}

function buildIntro({ businessName, businessType, city, missingWebsiteContext }) {
  const cleanBusinessName = normalize(businessName, "your business");
  const cleanBusinessType = normalize(businessType);
  const cleanCity = normalize(city);
  const cleanContext = normalize(
    missingWebsiteContext,
    "I noticed you may not have a dedicated website yet."
  );

  const descriptorParts = [cleanBusinessType, cleanCity].filter(Boolean);
  const descriptor = descriptorParts.length > 0
    ? `${descriptorParts.join(" ")} business`
    : "business";

  return `I was looking at ${cleanBusinessName}, and ${cleanContext} For a ${descriptor}, that usually means potential customers are missing an easy place to learn more, see what makes you different, and reach out directly.`;
}

function buildOfferParagraph({ offerSummary, customNotes }) {
  const cleanOffer = normalize(
    offerSummary,
    "building and setting up a personalized website for your business"
  );
  const cleanNotes = normalize(customNotes);

  const baseParagraph = `I help local businesses with ${cleanOffer}, keeping the setup straightforward so the site feels tailored to the business instead of looking like a generic template.`;

  if (!cleanNotes) {
    return baseParagraph;
  }

  return `${baseParagraph} ${toSentenceCase(cleanNotes)}`;
}

function buildSignature({ senderName, senderEmail, senderPhone, senderWebsite }) {
  const lines = [
    normalize(senderName, "Your Name"),
    normalize(senderEmail),
    normalize(senderPhone),
    normalize(senderWebsite),
  ].filter(Boolean);

  return lines.join("\n");
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function toHtml(text) {
  return text
    .split("\n\n")
    .map((paragraph) => `<p>${escapeHtml(paragraph).replace(/\n/g, "<br>")}</p>`)
    .join("\n");
}

function buildEmail(payload = {}) {
  const recipientName = normalize(payload.recipientName, "there");
  const callToAction = normalize(
    payload.callToAction,
    "If that is something you would be interested in, I would be happy to send over a few ideas tailored to your business."
  );

  const subject = buildSubject(payload);
  const text = [
    `Hi ${recipientName},`,
    buildIntro(payload),
    buildBenefitsParagraph(payload),
    buildOfferParagraph(payload),
    callToAction,
    `Best,\n${buildSignature(payload)}`,
  ].join("\n\n");

  return {
    subject,
    text,
    html: toHtml(text),
  };
}

module.exports = {
  buildEmail,
};
