import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
// import Sidebar from "@/components/Sidebar";
// import TinyRightSidebar from "@/components/TinyRightSidebar";

export const metadata: Metadata = {
  title: "YouPredict",
  description: "MLOps Portfolio Project",
};

// WITH BOTH SIDEBARS
///////////////////////////
// export default function RootLayout({
//   children,
// }: Readonly<{
//   children: React.ReactNode;
// }>) {
//   return (
//     <html lang="en">
//       <body className="antialiased">
//         <main className="flex flex-col h-screen bg-gray-50">
//           <Header />

//           <div className="flex flex-1 overflow-hidden">
//             <Sidebar />
//             <div className="flex-1 overflow-y-auto p-6">
//               {children}
//             </div>
//             <TinyRightSidebar />
//           </div>
//         </main>
//       </body>
//     </html>
//   );
// }

///////////////////////////
// WITHOUT BOTH SIDEBARS
///////////////////////////
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased font-normal text-gray-900">
        <main className="flex flex-col h-screen bg-gray-50">
          <Header />

          <div className="flex flex-1 overflow-hidden">
            {/* <Sidebar /> */}
            <div className="flex-1 overflow-y-auto bg-gray-100">{children}</div>
            {/* <TinyRightSidebar /> */}
          </div>
        </main>
      </body>
    </html>
  );
}
