-- Halaxy Clinic demo schema for Supabase (Postgres)
-- Run this entire file in Supabase Dashboard > SQL Editor > New query.
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null default 'Clinic user',
  email text not null,
  phone text default '',
  role text not null default 'patient' check (role in ('patient','doctor')),
  created_at timestamptz not null default now()
);
create table if not exists public.appointments (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid not null references public.profiles(id) on delete cascade,
  doctor_id uuid not null references public.profiles(id) on delete restrict,
  date date not null,
  time text not null,
  reason text default '',
  status text not null default 'Pending' check (status in ('Pending','Approved','Completed','Cancelled')),
  created_at timestamptz not null default now()
);
create table if not exists public.payments (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid not null references public.profiles(id) on delete cascade,
  amount numeric(10,2) not null default 0,
  method text not null default 'Not recorded',
  date date not null default current_date,
  status text not null default 'Unpaid' check (status in ('Paid','Unpaid')),
  created_at timestamptz not null default now()
);
create table if not exists public.clinic_settings (
  id text primary key default 'main' check (id='main'),
  name text not null default 'Halaxy Clinic',
  email text not null default '',
  phone text not null default '',
  address text not null default '',
  updated_by uuid references public.profiles(id),
  updated_at timestamptz not null default now()
);
insert into public.clinic_settings (id,name,email,phone,address) values ('main','Halaxy Clinic','','','') on conflict (id) do nothing;

-- Automatically create a patient profile after signup. Public signups cannot choose doctor role.
create or replace function public.handle_new_user() returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id,name,email,phone,role)
  values (new.id, coalesce(new.raw_user_meta_data->>'name','Clinic user'), new.email,
          coalesce(new.raw_user_meta_data->>'phone',''), 'patient')
  on conflict (id) do nothing;
  return new;
end; $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users for each row execute procedure public.handle_new_user();

alter table public.profiles enable row level security;
alter table public.appointments enable row level security;
alter table public.payments enable row level security;
alter table public.clinic_settings enable row level security;

-- Security-definer helper avoids recursive row-level-security checks on profiles.
create or replace function public.is_doctor() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.profiles where id=auth.uid() and role='doctor');
$$;
grant execute on function public.is_doctor() to authenticated;

-- Patient cancellation is restricted to changing status on their own pending appointment.
create or replace function public.cancel_own_pending_appointment(appointment_id uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  update public.appointments set status='Cancelled'
  where id=appointment_id and patient_id=auth.uid() and status='Pending';
  if not found then raise exception 'Appointment cannot be cancelled'; end if;
end; $$;
grant execute on function public.cancel_own_pending_appointment(uuid) to authenticated;

-- Profile: users can see their own record; doctors can see profiles for clinic administration.
drop policy if exists "profile self read" on public.profiles;
create policy "profile self read" on public.profiles for select to authenticated using (id=auth.uid() or role='doctor' or public.is_doctor());
drop policy if exists "profile self update" on public.profiles;
create policy "profile self update" on public.profiles for update to authenticated using (id=auth.uid()) with check (id=auth.uid() and role='patient');

-- Appointments: patients may create/view their own; doctors can view and manage all.
drop policy if exists "appointment read" on public.appointments;
create policy "appointment read" on public.appointments for select to authenticated using (patient_id=auth.uid() or public.is_doctor());
drop policy if exists "patient create appointment" on public.appointments;
create policy "patient create appointment" on public.appointments for insert to authenticated with check (patient_id=auth.uid() and exists (select 1 from public.profiles d where d.id=doctor_id and d.role='doctor'));
drop policy if exists "doctor update appointment" on public.appointments;
create policy "doctor update appointment" on public.appointments for update to authenticated using (public.is_doctor()) with check (public.is_doctor());
drop policy if exists "patient cancel pending appointment" on public.appointments;

-- Payments: users see their own; doctors can view and manage all payment rows.
drop policy if exists "payment read" on public.payments;
create policy "payment read" on public.payments for select to authenticated using (patient_id=auth.uid() or public.is_doctor());
drop policy if exists "doctor manage payments" on public.payments;
create policy "doctor manage payments" on public.payments for all to authenticated using (public.is_doctor()) with check (public.is_doctor());

-- Clinic settings are visible to signed-in users and editable by doctors only.
drop policy if exists "settings read" on public.clinic_settings;
create policy "settings read" on public.clinic_settings for select to authenticated using (true);
drop policy if exists "doctor update settings" on public.clinic_settings;
create policy "doctor update settings" on public.clinic_settings for all to authenticated using (public.is_doctor()) with check (public.is_doctor());
