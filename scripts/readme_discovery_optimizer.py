#!/usr/bin/env python3
import os
import re
import yaml

def read_file_content(filepath):
    """Reads content of a file."""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def check_one_sentence_description(readme_content):
    """Checks for a clear one-sentence description at the start of README."""
    if not readme_content:
        return "[FAIL] README.md пуст."
    
    first_heading_match = re.match(r'^#\s*(.*)', readme_content)
    if not first_heading_match:
        return "[FAIL] README.md не начинается с заголовка #."

    # Try to find the first sentence after the main heading
    lines = readme_content.split('\n')
    description_found = False
    for i, line in enumerate(lines):
        if line.strip().startswith('#'): # Skip headings
            continue
        if line.strip(): # Found a non-empty line
            first_sentence_match = re.match(r'^([^.!?]*[.!?:])', line.strip())
            if first_sentence_match:
                if len(first_sentence_match.group(1).split()) > 50: # Arbitrary word limit for "one sentence"
                    return "[FAIL] Первое предложение слишком длинное или нечеткое."
                return f"[PASS] Обнаружено четкое однопредложенческое описание: \"{first_sentence_match.group(1).strip()}\""
            else:
                return "[FAIL] Не удалось найти четкое однопредложенческое описание."
    return "[FAIL] Не удалось найти четкое однопредложенческое описание."


def check_install_command(readme_content):
    """Checks for 'hermes profile install' command near the top of README."""
    if not readme_content:
        return "[FAIL] README.md пуст."
    
    # Search within the first 100 lines (arbitrary "near the top")
    top_content = '\n'.join(readme_content.split('\n')[:100])
    if "hermes profile install" in top_content:
        return "[PASS] Команда 'hermes profile install' найдена в начале README.md."
    return "[FAIL] Команда 'hermes profile install' не найдена в начале README.md."

def check_github_topics(metadata_path="github-repo-metadata.yaml"):
    """Checks for github-repo-metadata.yaml and recommended topics."""
    metadata_content = read_file_content(metadata_path)
    if not metadata_content:
        return f"[FAIL] Файл {metadata_path} не найден."
    
    try:
        metadata = yaml.safe_load(metadata_content)
        topics = metadata.get("topics", [])
        
        recommended_topics = ["hermes-agent", "ai-agents", "agent-profile", "profile-distribution"]
        missing_topics = [t for t in recommended_topics if t not in topics]
        
        if not topics:
            return f"[FAIL] В {metadata_path} отсутствуют темы GitHub."
        if missing_topics:
            return f"[WARN] В {metadata_path} отсутствуют рекомендуемые темы: {', '.join(missing_topics)}."
        return f"[PASS] Обнаружены темы GitHub в {metadata_path} и все рекомендованные темы присутствуют."
    except yaml.YAMLError:
        return f"[FAIL] Некорректный формат YAML в {metadata_path}."

def check_domain_keywords_in_headings(readme_content, keywords=["Hermes", "Agent", "Profile", "Distribution"]):
    """Checks for domain keywords in README headings."""
    if not readme_content:
        return "[FAIL] README.md пуст."
    
    found_keywords = []
    for line in readme_content.split('\n'):
        if line.strip().startswith('#'):
            for keyword in keywords:
                if keyword.lower() in line.lower() and keyword not in found_keywords:
                    found_keywords.append(keyword)
    
    if found_keywords:
        return f"[PASS] Ключевые слова домена ({', '.join(found_keywords)}) найдены в заголовках README.md."
    return "[FAIL] Ключевые слова домена не найдены в заголовках README.md."

def check_source_template_lineage(readme_content):
    """Checks if hermes-profile-template is mentioned as a source."""
    if not readme_content:
        return "[FAIL] README.md пуст."
    
    if "hermes-profile-template" in readme_content:
        return "[PASS] 'hermes-profile-template' упоминается в README.md как источник/шаблон."
    return "[FAIL] 'hermes-profile-template' не упоминается в README.md как источник/шаблон."

def check_validation_smoke_commands(readme_content):
    """Checks for mentions of validation and smoke commands."""
    if not readme_content:
        return "[FAIL] README.md пуст."
    
    validation_found = "scripts/validate_profile.py" in readme_content or "make validate" in readme_content
    smoke_found = "scripts/smoke_install.sh" in readme_content or "make smoke" in readme_content
    
    if validation_found and smoke_found:
        return "[PASS] Команды валидации и smoke-тестов найдены в README.md."
    if validation_found:
        return "[WARN] Команды валидации найдены, но команды smoke-тестов отсутствуют."
    if smoke_found:
        return "[WARN] Команды smoke-тестов найдены, но команды валидации отсутствуют."
    return "[FAIL] Команды валидации и smoke-тестов не найдены в README.md."

def check_license_security_docs():
    """Checks for existence of LICENSE and SECURITY.md."""
    license_exists = os.path.exists("LICENSE")
    security_exists = os.path.exists("SECURITY.md")
    
    if license_exists and security_exists:
        return "[PASS] Файлы LICENSE и SECURITY.md существуют."
    if license_exists:
        return "[WARN] Файл LICENSE существует, но SECURITY.md отсутствует."
    if security_exists:
        return "[WARN] Файл SECURITY.md существует, но LICENSE отсутствует."
    return "[FAIL] Файлы LICENSE и SECURITY.md отсутствуют."

def check_social_preview_guidance(readme_content):
    """Checks for social media preview guidance in README."""
    if not readme_content:
        return "[FAIL] README.md пуст."
    
    if "Social Media & Share Previews" in readme_content and "og:image" in readme_content:
        return "[PASS] Руководство по социальным сетям и превью найдено в README.md."
    return "[FAIL] Руководство по социальным сетям и превью не найдено в README.md."

def generate_report(results):
    """Generates a Markdown report."""
    report = "# Отчет об Оптимизации Обнаружения README.md\n\n"
    report += "## Проверки\n\n"
    for check, status in results.items():
        report += f"- {status} {check}\n"
    
    report += "\n## Резюме\n\n"
    failures = [s for s in results.values() if s.startswith("[FAIL]")]
    warnings = [s for s in results.values() if s.startswith("[WARN]")]
    
    if not failures and not warnings:
        report += "Все проверки пройдены успешно. README.md хорошо оптимизирован для обнаружения.\n"
    elif not failures and warnings:
        report += "Некоторые проверки имеют предупреждения. Рассмотрите возможность их улучшения для лучшей обнаруживаемости.\n"
    else:
        report += "Обнаружены ошибки. Пожалуйста, просмотрите отчет и исправьте их для улучшения обнаруживаемости.\n"
    return report

def main():
    print("Начинаю анализ README.md для оптимизации обнаружения...")
    
    readme_content = read_file_content("README.md")
    
    results = {}
    results["Описание из одного предложения"] = check_one_sentence_description(readme_content)
    results["Команда установки"] = check_install_command(readme_content)
    results["Темы GitHub"] = check_github_topics()
    results["Ключевые слова домена в заголовках"] = check_domain_keywords_in_headings(readme_content)
    results["Родословная исходного шаблона"] = check_source_template_lineage(readme_content)
    results["Команды валидации и smoke-тестов"] = check_validation_smoke_commands(readme_content)
    results["Документы по лицензии и безопасности"] = check_license_security_docs()
    results["Руководство по социальным сетям и превью"] = check_social_preview_guidance(readme_content)
    
    report = generate_report(results)
    print("\n" + report)
    with open("readme_discovery_report.md", "w", encoding='utf-8') as f:
        f.write(report)
    print("Отчет сохранен в readme_discovery_report.md")

if __name__ == "__main__":
    main()
