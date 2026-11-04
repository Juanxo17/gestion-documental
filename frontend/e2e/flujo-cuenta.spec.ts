import { type Page, expect, test } from "@playwright/test";

const CONTRASENA = process.env.E2E_CONTRASENA ?? "Demo2025*";
const ADMINISTRADORA = "ana.rodriguez@entidad.gov.co";
const REVISORA = "maria.cifuentes@entidad.gov.co";

async function entrar(page: Page, correo: string) {
  await page.goto("/login");
  await page.getByLabel("Correo").fill(correo);
  await page.getByLabel("Contraseña").fill(CONTRASENA);
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page.getByRole("heading", { name: "Resumen" })).toBeVisible();
}

async function salir(page: Page) {
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page.getByRole("button", { name: "Ingresar" })).toBeVisible();
}

test("login, radicar y aprobar una cuenta", async ({ page }) => {
  const radicado = `RAD-E2E-${Date.now()}`;

  await entrar(page, ADMINISTRADORA);
  await page.getByRole("link", { name: "Cuentas de cobro" }).click();
  await page.getByRole("link", { name: "Radicar cuenta" }).click();
  await page.getByLabel("Contrato (solo activos)").selectOption("CONT-2025-004");
  await page.getByLabel("Número de radicado").fill(radicado);
  await page.getByLabel("Número de cuenta").fill(radicado.replace("RAD", "CTA"));
  await page.getByLabel("Valor a cobrar").fill("1000");
  await page.getByLabel("Fecha de presentación").fill("2025-06-15");
  await page.getByLabel("Concepto de pago").fill("Prueba automatizada de radicación");
  await page.getByRole("button", { name: "Radicar" }).click();
  await expect(page.getByRole("heading", { name: `Cuenta ${radicado}` })).toBeVisible();
  await salir(page);

  await entrar(page, REVISORA);
  await page.goto(`/cuentas/${radicado}`);
  await page.getByRole("button", { name: "Enviar a revisión" }).click();
  await expect(page.getByText("Enviar a revisión: listo.")).toBeVisible();
  await page.getByRole("button", { name: "Aprobar" }).click();
  await expect(page.getByText("Aprobar: listo.")).toBeVisible();
  await expect(page.getByRole("heading", { name: `Cuenta ${radicado}` })).toBeVisible();
  await expect(page.locator("main").getByText("Aprobada").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Registrar pago" })).toHaveCount(0);
});

test("credenciales incorrectas muestran el mensaje del backend", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Correo").fill("nadie@entidad.gov.co");
  await page.getByLabel("Contraseña").fill("equivocada");
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page.getByText("Correo o contraseña incorrectos")).toBeVisible();
});
