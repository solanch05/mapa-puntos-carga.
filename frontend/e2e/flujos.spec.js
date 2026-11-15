/**
 * Flujos principales del demo (sección 7). El flujo 1 + reportar estado es
 * "el flujo que no puede romperse" (sección 9).
 *
 * Usuarios de `sembrar_demo`: ana@demo.local (de confianza) y luis@demo.local
 * (nuevo), contraseña Demo1234!
 */

import { expect, test } from '@playwright/test'

const CLAVE = 'Demo1234!'

async function entrar(page, email) {
  await page.goto('/entrar')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Contraseña').fill(CLAVE)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/$/)
}

test('Flujo 1 · de la pantalla de inicio a la ficha en menos de 30 segundos', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: /Con energía ahora/ }).click()
  await expect(page.getByText(/punto\(s\) en esta zona/)).toBeVisible()

  // Abrimos la lista (más fiable que tocar un círculo del mapa) y elegimos el primero.
  await page.getByRole('button', { name: 'Lista' }).click()
  const primero = page.getByRole('list', { name: 'Puntos cercanos' }).getByRole('button').first()
  await expect(primero).toContainText('Con energía')
  await primero.click()

  const ficha = page.getByRole('complementary')
  await expect(ficha.getByTestId('estado-actual')).toContainText('confirmado hace')
  await expect(ficha.getByRole('link', { name: /Cómo llegar/ })).toHaveAttribute('href', /maps/)

  const segundos = await page.evaluate(() => window.__segundosHastaFicha)
  expect(segundos).toBeLessThan(30)
})

test('Flujo 3 · confirmar el estado en un toque', async ({ page }) => {
  await entrar(page, 'ana@demo.local')
  await page.getByRole('button', { name: 'Lista' }).click()
  await page.getByRole('button', { name: /Barbería Los Amigos/ }).click()

  const ficha = page.getByRole('complementary')
  await expect(ficha.getByTestId('estado-actual')).toContainText('Sin confirmar')
  await ficha.getByRole('region', { name: '¿Hay corriente ahora?' }).getByRole('button', { name: 'Con energía' }).click()

  await expect(ficha.getByText(/¡Gracias!/)).toBeVisible()
  await expect(ficha.getByTestId('estado-actual')).toContainText('Con energía')
  await expect(ficha.getByTestId('estado-actual')).toContainText('confirmado hace')
})

test('Flujo 2 · compartir un punto queda pendiente de revisión', async ({ page }) => {
  await entrar(page, 'luis@demo.local')
  await page.goto('/agregar')
  await page.getByLabel('Nombre del lugar').fill(`Casa de prueba ${Date.now()}`)
  await page.getByLabel('Tipo de lugar').selectOption('vivienda')
  await expect(page.getByText(/ubicación aproximada/)).toBeVisible()

  const mapa = page.getByTestId('selector-ubicacion')
  await mapa.click({ position: { x: 120, y: 100 } })
  await expect(page.getByText(/Pin en/)).toBeVisible()

  await page.getByRole('button', { name: 'Enviar punto' }).click()
  await expect(page).toHaveURL(/mis-puntos/)
  await expect(page.getByText(/pendiente de revisión/i).first()).toBeVisible()
})
