import json
import re
import os
import sys
import io
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Any
from openai import OpenAI
from dotenv import load_dotenv
import datetime


from src.ingestion.law_parser import LawParser

# Fix path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


class DocumentAnalyzer:
    """Analyzes legal documents for loopholes, mistakes, and risks."""
    
    def __init__(self):
        self.client = OpenAI(
            base_url="https://tokenfactory.esprit.tn/api", 
            api_key=os.getenv("ESPRIT_LLM_API_KEY")
        )
        self.model = "hosted_vllm/Llama-3.1-70B-Instruct"
        self.parser = LawParser()
        
    
    
    def _analyze_with_llm(self, markup: str, document_type: str = "legal") -> Dict[str, Any]:
        """Analyze document markup using LLM for risks and loopholes."""
        logger.info("Starting LLM analysis of document")
        
        analysis_prompt = f"""
        Tu es un expert juridique spécialisé en analyse de risques documentaires.
        Analyse le contrat suivant pour identifier les loopholes, erreurs, ambiguïtés et risques légaux.
        
        DOCUMENT:
        {markup[:5000]}  # Limit to first 5000 chars to avoid token limits
        
        Fournis une analyse structurée en JSON avec exactement ces champs:
        {{
            "risk_score": 0.0,  # Score entre 0.0 (aucun risque) et 1.0 (risque critique)
            "risk_level": "Low|Medium|High|Critical",
            "document_type": "{document_type}",
            "loopholes": [
                {{
                    "title": "Nom du loophole",
                    "description": "Description détaillée",
                    "severity": "Low|Medium|High|Critical",
                    "location": "Où dans le document (numéro de section/article si possible)"
                }}
            ],
            "errors": [
                {{
                    "type": "Type d'erreur (grammatical, légal, contradiction, etc.)",
                    "description": "Description de l'erreur",
                    "location": "Où dans le document"
                }}
            ],
            "missing_elements": [
                "Élément manquant 1",
                "Élément manquant 2"
            ],
            "suggestions": [
                {{
                    "priority": "High|Medium|Low",
                    "suggestion": "Suggestion d'amélioration détaillée"
                }}
            ],
            "summary": "Résumé des risques principaux et recommandations"
        }}
        
        Sois rigoureux mais juste. Identifie les vrais problèmes seulement.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Tu es un expert juridique spécialisé en analyse de risques."},
                    {"role": "user", "content": analysis_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000
            )
            
            analysis = json.loads(response.choices[0].message.content)
            logger.info("LLM analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error("LLM analysis failed: %s", str(e))
            raise
    
    def _score_document_structure(self, markup: str) -> Dict[str, Any]:
        """Analyze document structure for completeness and proper organization."""
        logger.info("Analyzing document structure")
        
        structure_score = {
            "has_title": 0.0,
            "has_sections": 0.0,
            "has_numbering": 0.0,
            "readability": 0.0,
            "formatting_consistency": 0.0
        }
        
        # Check for title
        lines = markup.split('\n')
        if any(line.startswith('# ') for line in lines[:10]):
            structure_score["has_title"] = 1.0
        
        # Check for sections
        section_count = len([l for l in lines if l.startswith('#')])
        structure_score["has_sections"] = min(1.0, section_count / 5)
        
        # Check for numbering (articles, clauses, etc.)
        numbered_items = len(re.findall(r'(Article|Section|Clause|Paragraph|\d+\.)', markup))
        structure_score["has_numbering"] = min(1.0, numbered_items / 20)
        
        # Readability (average line length, paragraph structure)
        non_empty_lines = [l for l in lines if l.strip()]
        avg_length = sum(len(l) for l in non_empty_lines) / len(non_empty_lines) if non_empty_lines else 0
        structure_score["readability"] = 1.0 if 50 < avg_length < 200 else 0.5
        
        # Formatting consistency (check for markdown consistency)
        bold_count = len(re.findall(r'\*\*[^*]+\*\*', markup))
        italic_count = len(re.findall(r'\*[^*]+\*', markup))
        list_count = len(re.findall(r'^\s*[-*]\s', markup, re.MULTILINE))
        structure_score["formatting_consistency"] = min(1.0, (bold_count + italic_count + list_count) / 10)
        
        overall_structure_score = sum(structure_score.values()) / len(structure_score)
        
        logger.info("Structure analysis completed: %.2f", overall_structure_score)
        return {
            "structure_scores": structure_score,
            "overall_structure_score": overall_structure_score
        }
    
    def analyze(self, file_content: bytes, filename: str = "document.pdf", document_type: str = "legal") -> Dict[str, Any]:
        """
        Complete analysis pipeline for a document.
        
        Args:
            file_path: Path to PDF or image file
            document_type: Type of document (legal, contract, policy, etc.)
            
        Returns:
            Comprehensive analysis report with risk scores and suggestions
        """
        
        logger.info("=== Document Analysis Started ===")
        logger.info("File: %s, Type: %s", filename, document_type)
        
        try:
            # 1. Extraction du contenu (Markup/Markdown)
            # On passe le file_path. La conversion en BytesIO se fera à l'intérieur du parser.
            logger.info("Extracting text and structure from document...")
            markup = self.parser.export_markdown(file_content)
            
            if not markup or len(markup.strip()) == 0:
                logger.warning("No content could be extracted from the document.")
            
            # 2. Analyse de la structure (Scores heuristiques)
            logger.info("Scoring document structure...")
            structure_analysis = self._score_document_structure(markup)
            
            # 3. Analyse par l'IA (Analyse de risque et clauses)
            logger.info("Performing LLM analysis for risk and legal logic...")
            llm_analysis = self._analyze_with_llm(markup, document_type)
            
            # 4. Calcul du score de risque global
            # Logique : 70% basé sur l'IA, 30% basé sur la qualité de la structure
            risk_score = llm_analysis.get("risk_score", 0.5)
            structure_score = structure_analysis.get("overall_structure_score", 0.5)
            
            overall_risk_score = (risk_score * 0.7) + ((1.0 - structure_score) * 0.3)
            
            # 5. Compilation du rapport final
            final_report = {
                "file": filename,
                "document_type": document_type,
                "analysis_timestamp": str(datetime.datetime.now()),
                "markup_length": len(markup),
                "structure_analysis": structure_analysis,
                "risk_analysis": llm_analysis,
                "overall_risk_score": round(overall_risk_score, 2),
                "summary": llm_analysis.get("summary", "Pas de résumé disponible.")
            }
            
            logger.info("=== Document Analysis Completed ===")
            logger.info("Overall Risk Score: %.2f, Risk Level: %s", 
                        final_report["overall_risk_score"],
                        llm_analysis.get("risk_level", "Unknown"))
            
            return final_report
            
        except Exception as e:
            logger.error("Document analysis failed: %s", str(e), exc_info=True)
            raise


def analyze_document(file_path: str, document_type: str = "legal") -> Dict[str, Any]:
    """Fonction de commodité : on repasse le simple chemin (string)"""
    analyzer = DocumentAnalyzer()
    # On envoie le 'file_path' qui est bien une chaîne de caractères
    return analyzer.analyze(file_path, document_type)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python doc_analyzer.py <file_path> [document_type]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    doc_type = sys.argv[2] if len(sys.argv) > 2 else "legal"
    
    report = analyze_document(file_path, doc_type)
    
    # Print formatted report
    print("\n" + "="*60)
    print("DOCUMENT ANALYSIS REPORT")
    print("="*60)
    print(f"File: {report['file']}")
    print(f"Document Type: {report['document_type']}")
    print(f"Overall Risk Score: {report['overall_risk_score']:.2f}")
    print(f"Risk Level: {report['risk_analysis'].get('risk_level', 'Unknown')}")
    print("\nStructure Analysis:")
    for key, value in report['structure_analysis']['structure_scores'].items():
        print(f"  {key}: {value:.2f}")
    
    if report['risk_analysis'].get('loopholes'):
        print("\nLoopholes Found:")
        for loophole in report['risk_analysis']['loopholes']:
            print(f"  - {loophole['title']} ({loophole['severity']})")
            print(f"    {loophole['description']}")
    
    if report['risk_analysis'].get('suggestions'):
        print("\nTop Suggestions:")
        for i, suggestion in enumerate(report['risk_analysis']['suggestions'][:3], 1):
            print(f"  {i}. [{suggestion['priority']}] {suggestion['suggestion']}")
    
    print("\nFull Report:")
    print(json.dumps(report, ensure_ascii=False, indent=2))
