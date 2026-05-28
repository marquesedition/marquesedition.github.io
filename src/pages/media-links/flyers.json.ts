import flyersPayload from "../../data/flyers.json";

export const prerender = true;

export function GET() {
  return new Response(JSON.stringify(flyersPayload, null, 2), {
    headers: {
      "content-type": "application/json; charset=utf-8",
    },
  });
}
