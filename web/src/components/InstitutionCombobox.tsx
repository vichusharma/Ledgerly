"use client";

import { useState, useRef, useEffect } from "react";

export const FR_BANKS = [
  // Major national banks (default top 10)
  "BNP Paribas",
  "Crédit Agricole",
  "Société Générale",
  "Caisse d'Épargne",
  "Banque Populaire",
  "Crédit Mutuel",
  "LCL",
  "La Banque Postale",
  "CIC",
  "HSBC France",
  // Online & challenger banks
  "Boursorama Banque",
  "Hello bank!",
  "Fortuneo",
  "Monabanq",
  "N26",
  "Revolut",
  "Qonto",
  "Shine",
  "Sumeria",
  "Nickel",
  "Ma French Bank",
  "Blank",
  "Memo Bank",
  "Anytime",
  // Regional Crédit Agricole
  "Crédit Agricole Alpes Provence",
  "Crédit Agricole Alsace Vosges",
  "Crédit Agricole Aquitaine",
  "Crédit Agricole Atlantique Vendée",
  "Crédit Agricole Brie Picardie",
  "Crédit Agricole Bretagne",
  "Crédit Agricole Centre France",
  "Crédit Agricole Centre Loire",
  "Crédit Agricole Centre Ouest",
  "Crédit Agricole Centre-Est",
  "Crédit Agricole Charente-Maritime Deux-Sèvres",
  "Crédit Agricole Charente-Périgord",
  "Crédit Agricole Côtes d'Armor",
  "Crédit Agricole des Savoie",
  "Crédit Agricole du Finistère",
  "Crédit Agricole du Languedoc",
  "Crédit Agricole du Morbihan",
  "Crédit Agricole Franche-Comté",
  "Crédit Agricole Guadeloupe",
  "Crédit Agricole Île-de-France",
  "Crédit Agricole Ille-et-Vilaine",
  "Crédit Agricole Loire Haute-Loire",
  "Crédit Agricole Lorraine",
  "Crédit Agricole Martinique Guyane",
  "Crédit Agricole Nord Est",
  "Crédit Agricole Nord Midi-Pyrénées",
  "Crédit Agricole Nord de France",
  "Crédit Agricole Normandie",
  "Crédit Agricole Normandie Seine",
  "Crédit Agricole Provence Côte d'Azur",
  "Crédit Agricole Pyrénées Gascogne",
  "Crédit Agricole Réunion",
  "Crédit Agricole Sud Méditerranée",
  "Crédit Agricole Sud Rhône Alpes",
  "Crédit Agricole Toulouse 31",
  "Crédit Agricole Val de France",
  // Regional Banque Populaire
  "Banque Populaire Auvergne Rhône Alpes",
  "Banque Populaire Bourgogne Franche-Comté",
  "Banque Populaire Grand Ouest",
  "Banque Populaire Méditerranée",
  "Banque Populaire Nord",
  "Banque Populaire Occitane",
  "Banque Populaire Rives de Paris",
  "Banque Populaire Sud",
  "Banque Populaire Val de France",
  "BRED Banque Populaire",
  "CASDEN Banque Populaire",
  // Regional Caisse d'Épargne
  "Caisse d'Épargne Alsace",
  "Caisse d'Épargne Aquitaine Poitou-Charentes",
  "Caisse d'Épargne Auvergne et Limousin",
  "Caisse d'Épargne Bourgogne Franche-Comté",
  "Caisse d'Épargne Bretagne Pays de Loire",
  "Caisse d'Épargne Côte d'Azur",
  "Caisse d'Épargne Grand Est Europe",
  "Caisse d'Épargne Hauts de France",
  "Caisse d'Épargne Île-de-France",
  "Caisse d'Épargne Loire-Centre",
  "Caisse d'Épargne Loire Drôme Ardèche",
  "Caisse d'Épargne Midi-Pyrénées",
  "Caisse d'Épargne Normandie",
  "Caisse d'Épargne Provence-Alpes-Corse",
  "Caisse d'Épargne Rhône Alpes",
  // Regional Crédit Mutuel
  "Crédit Mutuel Arkéa",
  "Crédit Mutuel Bretagne",
  "Crédit Mutuel Centre Est Europe",
  "Crédit Mutuel du Sud Ouest",
  "Crédit Mutuel Loire-Atlantique et Centre Ouest",
  "Crédit Mutuel Maine-Anjou Basse-Normandie",
  "Crédit Mutuel Midi-Atlantique",
  "Crédit Mutuel Nord Europe",
  "Crédit Mutuel Normand",
  "Crédit Mutuel Océan",
  "Crédit Mutuel Savoie-Mont Blanc",
  // CIC regional
  "CIC Est",
  "CIC Lyonnaise de Banque",
  "CIC Nord Ouest",
  "CIC Ouest",
  "CIC Sud Ouest",
  // International banks with French branches
  "ABN AMRO France",
  "Barclays France",
  "BBVA France",
  "Citibank France",
  "Deutsche Bank France",
  "Goldman Sachs France",
  "ING France",
  "JPMorgan Chase France",
  "Morgan Stanley France",
  "Santander France",
  "UBS France",
  // Insurance-backed banks
  "AXA Banque",
  "Allianz Banque",
  "Groupama Banque",
  "MAAF Banque",
  "MIF Banque",
  // Cooperative & mutual
  "Crédit Coopératif",
  "Crédit Maritime Mutuel",
  "Banque Française Mutualiste",
  // Private & wealth management
  "Banque Delubac & Cie",
  "Banque Neuflize OBC",
  "Banque Palatine",
  "Banque Richelieu France",
  "Banque Transatlantique",
  "Edmond de Rothschild",
  "Lazard Frères Banque",
  "Milleis Banque",
  "Rothschild & Co",
  "Société Marseillaise de Crédit",
  // Consumer credit & auto finance
  "Cetelem",
  "Cofidis",
  "Floa Banque",
  "Franfinance",
  "My Money Bank",
  "PSA Banque France",
  "RCI Banque",
  "Sofinco",
  "Younited Credit",
  // Public & development
  "Bpifrance",
  "Caisse des Dépôts et Consignations",
  "Natixis",
  // Overseas
  "Banque des Antilles Françaises",
  "BNP Paribas Réunion",
  "Banque de la Réunion",
  "Crédit Agricole de la Réunion",
  "Société Générale Guadeloupe",
  "Société Générale Martinique",
];

export function InstitutionCombobox({ value, onChange, placeholder, inputClass }: {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  inputClass: string;
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const matches = value.trim() === ""
    ? FR_BANKS.slice(0, 10)
    : FR_BANKS.filter(b => b.toLowerCase().includes(value.toLowerCase())).slice(0, 10);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <input
        value={value}
        onChange={e => { onChange(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onKeyDown={e => { if (e.key === "Escape") setOpen(false); }}
        className={inputClass}
        placeholder={placeholder}
        autoComplete="off"
      />
      {open && matches.length > 0 && (
        <ul className="absolute z-50 mt-1 w-full bg-white dark:bg-secondary border border-surface-border dark:border-border rounded-lg shadow-lg overflow-hidden max-h-52 overflow-y-auto">
          {matches.map(bank => (
            <li key={bank}>
              <button
                type="button"
                className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-muted text-slate-800 dark:text-foreground"
                onMouseDown={e => {
                  e.preventDefault();
                  onChange(bank);
                  setOpen(false);
                }}
              >
                {bank}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
