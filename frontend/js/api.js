class ApiClientError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
  }
}

function describeApiDetail(detail) {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((issue) => {
        const location = Array.isArray(issue.loc)
          ? issue.loc.filter((part) => part !== "body").join(".")
          : "";
        return location ? `${location}: ${issue.msg}` : issue.msg;
      })
      .filter(Boolean)
      .join(" ");
  }
  if (detail && typeof detail === "object") {
    const message = detail.message || "The request could not be completed.";
    const missingMeals = Array.isArray(detail.missing_meals)
      ? ` No eligible foods for: ${detail.missing_meals.join(", ")}.`
      : "";
    return missingMeals && !message.includes(detail.missing_meals.join(", "))
      ? `${message}${missingMeals}`
      : message;
  }
  return "The request could not be completed.";
}

async function requestJson(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiClientError(
        "Could not reach the server. Check that the FastAPI app is running.",
      );
    }
    throw error;
  }

  const responseText = await response.text();
  let result = null;
  if (responseText) {
    try {
      result = JSON.parse(responseText);
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new ApiClientError(
          "The server returned an unreadable response.",
          response.status,
        );
      }
      throw error;
    }
  }

  if (!response.ok) {
    throw new ApiClientError(
      describeApiDetail(result && result.detail),
      response.status,
    );
  }
  return result;
}

window.apiClient = {
  get(path) {
    return requestJson(path);
  },
  post(path, payload) {
    return requestJson(path, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
