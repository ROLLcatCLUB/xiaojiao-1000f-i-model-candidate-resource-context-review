from __future__ import annotations
import argparse, json, sys, zipfile
from pathlib import Path
STAGE='1000H_MODEL_CANDIDATE_REQUEST_ENVELOPE_DRY_RUN'
FINAL='XIAOJIAO_MODEL_CANDIDATE_REQUEST_ENVELOPE_DRY_RUN_PASS'
SLUG='xiaojiao_model_candidate_request_envelope_dry_run_1000H'
MARKER='ALL_1000H_MODEL_CANDIDATE_REQUEST_ENVELOPE_DRY_RUN_CHECKS_OK'
SAMPLE='model_candidate_request_envelope_dry_run_1000H.json'
BAD_PARTS=['.env','token','secret','key','node_modules','__pycache__','.db','.sqlite','dist','build','coverage','.DS_Store']
FORBIDDEN=['full_chat_history','full_work_state_dump','raw_database_dump','unrelated_lessons','unrelated_teacher_private_data','direct_memory_write','direct_frontend_control','direct_export']
def fail(m): raise SystemExit(f'VALIDATION_FAILED: {m}')
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); a=ap.parse_args(); root=Path(a.root).resolve() if a.root else Path(__file__).resolve().parents[1]
    req=['docs/audit/xiaojiao_1001_state_driven_intelligence_engine_fixture_baseline_summary.json',f'docs/foundation/{SLUG}.md',f'docs/foundation/{SLUG}.json',f'samples/{SLUG}/{SAMPLE}',f'docs/audit/{SLUG}_result.json',f'docs/audit/{SLUG}_report.md',f'docs/audit_packages/{SLUG}_manifest.json',f'scripts/validate_{SLUG}.py']
    for r in req:
        if not (root/r).exists(): fail(f'missing required file: {r}')
    summary=load(root/'docs/audit/xiaojiao_1001_state_driven_intelligence_engine_fixture_baseline_summary.json')
    if summary.get('summary_code')!='1001_STATE_DRIVEN_INTELLIGENCE_ENGINE_FIXTURE_BASELINE_PASS' or summary.get('real_engine_implemented') is not False: fail('1001 summary gate mismatch')
    contract=load(root/f'docs/foundation/{SLUG}.json'); sample=load(root/f'samples/{SLUG}/{SAMPLE}'); result=load(root/f'docs/audit/{SLUG}_result.json'); manifest=load(root/f'docs/audit_packages/{SLUG}_manifest.json')
    if contract.get('stage_code')!=STAGE or result.get('stage_code')!=STAGE or sample.get('stage_code')!=STAGE: fail('stage identity mismatch')
    if result.get('final_status')!=FINAL or result.get('pass') is not True or result.get('marker')!=MARKER: fail('result mismatch')
    for container in [contract.get('hard_boundaries',{}), result.get('boundary_flags',{}), sample.get('boundary_flags', sample.get('safety_boundary',{}))]:
        for k,v in container.items():
            if v is not False and (k.endswith('_allowed') or k.endswith('_called') or k.endswith('_written') or k.endswith('_created') or k.endswith('_connected') or k.endswith('_modified') or k.endswith('_entered') or k.endswith('_performed') or k.endswith('_configured')): fail(f'unsafe boundary {k}')
    if STAGE.startswith('1000F'):
        if set(contract.get('resource_context_registry',[])) != {'textbook_catalog_resource','school_calendar_resource','lesson_plan_resource','handout_resource','rubric_resource','curriculum_standard_resource','teacher_preference_candidate_resource','work_state_snapshot_resource'}: fail('resource registry mismatch')
        for key in ['resource_context_registry','resource_context_ref_schema','allowed_resource_refs','forbidden_resource_refs','context_pack_policy','model_candidate_envelope','token_budget_policy','safety_boundary','no_direct_provider_call_policy']:
            if key not in sample: fail(f'missing {key}')
    elif STAGE.startswith('1000G'):
        tasks=sample.get('tasks',[])
        if {t.get('task_id') for t in tasks}!={'generate_teaching_work_plan','generate_lesson_plan','generate_handout','revise_lesson_section','ask_lesson_optimization_question'}: fail('task coverage mismatch')
        for t in tasks:
            for k in ['task_id','parsed_intent','target_work_object','required_resource_refs','optional_resource_refs','excluded_resource_refs','context_pack','estimated_token_budget','trim_reason','forbidden_context_removed']:
                if k not in t: fail(f"{t.get('task_id')} missing {k}")
            if t.get('forbidden_context_removed') is not True: fail('forbidden context not removed')
            if set(t.get('context_pack',{}).keys()) & set(FORBIDDEN): fail('forbidden context leaked')
    elif STAGE.startswith('1000H'):
        reqs=sample.get('candidate_requests',[])
        if len(reqs)<4: fail('candidate request coverage too small')
        for r in reqs:
            for k in ['request_id','task_type','target_work_object','context_pack_ref','prompt_policy_ref','input_summary','expected_output_schema','token_budget','cost_tier_candidate','provider_allowed','provider_called','model_called','generated_content_absent','expected_result_route']:
                if k not in r: fail(f"{r.get('request_id')} missing {k}")
            if r.get('provider_allowed') is not False or r.get('provider_called') is not False or r.get('model_called') is not False or r.get('generated_content_absent') is not True: fail('candidate boundary mismatch')
            if not isinstance(r.get('expected_output_schema'), list) or 'review_required' not in r.get('expected_output_schema',[]) and 'teacher_review_required' not in r.get('expected_output_schema',[]): fail('schema review gate missing')
    elif STAGE.startswith('1000I'):
        results=sample.get('simulated_candidate_results',[])
        if len(results)<4: fail('simulated result coverage too small')
        for r in results:
            for step in ['candidate_result_received','schema_validation','normalization','safety_check']:
                if step not in r: fail(f"{r.get('result_id')} missing {step}")
            patch=r.get('work_object_patch',{})
            if r.get('teacher_review_required') is not True or r.get('formal_write_performed') is not False or r.get('database_written') is not False or r.get('memory_written') is not False or r.get('frontend_direct_update') is not False: fail('write boundary mismatch')
            if patch.get('review_status')!='pending_teacher_review' or patch.get('applied') is not False or patch.get('rollback_available') is not True: fail('patch review gate mismatch')
    z=root/f'docs/audit_packages/{SLUG}.zip'
    if not z.exists(): fail('missing zip')
    with zipfile.ZipFile(z) as zf: entries=zf.namelist()
    for e in entries:
        n=e.replace('\\','/')
        if n.startswith('/') or ':' in n or '\\' in e: fail(f'unsafe zip path {e}')
        if any(b.lower() in n.lower() for b in BAD_PARTS): fail(f'forbidden zip entry {e}')
    if manifest.get('manifest_minus_zip')!=[] or manifest.get('zip_minus_manifest')!=[] or sorted(manifest.get('zip_entries',[]))!=sorted(entries): fail('manifest zip mismatch')
    print(MARKER); return 0
if __name__=='__main__': sys.exit(main())