import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "Weather Data Analysis | WeatherPulse", description: "Historical weather analytics, city comparisons, model evaluation and Hadoop storage insights." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
